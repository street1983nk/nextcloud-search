/**
 * The refresh of blocks one to three, the lookup of block four and the rules
 * form of block five, in plain browser JavaScript.
 *
 * No module, no bundler, no dependency and no package file anywhere in this
 * app: the page is a PHP template, the Nextcloud server CSS and this file. The
 * script never builds markup. Everything it touches already exists in the
 * template, rendered server side with real values, so the page is complete
 * before this file has run and stays complete if it never runs at all.
 *
 * The one element that has to come into existence at runtime is a row of the
 * exclusion list, and it is cloned from the template element of the page rather
 * than assembled from a string. Its two variable parts are a text node and an
 * aria-label, so a folder name cannot become an element here no matter what
 * characters it contains. That is what keeps the markup assigning properties of
 * an element out of this file altogether, and Gate C in
 * backend/tests/test_admin_ui_contract.py holds it: the gate matches on their
 * names as plain text, so they may not even be named in a comment.
 *
 * Sources of the two facts that are easy to get wrong:
 *   core/templates/layout.initial-state.php   the hidden input, its id, base64
 *   core/src/OC/requesttoken.ts               the token and its rotation
 *   core/templates/layout.user.php            the locale on the root element
 */
'use strict'

;(function () {
  // Five seconds while there is work in the queue, thirty once there is not.
  // The page is rarely open, but when it is, the admin wants to see progress.
  const POLL_ACTIVE_MS = 5000
  const POLL_IDLE_MS = 30000

  // After this many polls in a row that changed nothing, the fast cadence stops
  // being useful and the page falls back to the slow one. Nothing polls a
  // resting instance every five seconds forever.
  const UNCHANGED_LIMIT = 20

  const SECONDS_PER_MINUTE = 60
  const SECONDS_PER_HOUR = 3600
  const SECONDS_PER_DAY = 86400

  // The same unit table the template uses, so that a size does not change its
  // shape when the first poll arrives. The symbols are not translated, in
  // Nextcloud either.
  const SIZE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
  const BYTES_PER_UNIT = 1024

  // The four addresses this page asks, written out whole rather than assembled
  // from a prefix and a name: a grep for either route has to find its caller,
  // and a route that is only half spelled anywhere is a route nobody finds when
  // it moves.
  const ROUTE_OVERVIEW = 'admin/overview'
  const ROUTE_DIAGNOSE = 'admin/diagnose'
  const ROUTE_RULES = 'admin/rules'
  const ROUTE_RULES_PREVIEW = 'admin/rules/preview'
  // The two addresses of the block "Performance profile" (plan 27-07): the
  // probe, started by a POST and read by a GET, and the way down without one.
  const ROUTE_PROFILE = 'admin/profile'
  const ROUTE_PROFILE_CHECK = 'admin/profile/check'

  // How often the state of a running probe is asked, and never slower than the
  // active cadence of the status poll: the admin who pressed the button is
  // watching the progress line (D-27-06, D-27-16).
  const POLL_PROBE_MS = 2000

  // Polls in a row that report no running probe and no new result before the
  // page stops waiting for one. A start the container accepted is running on
  // the next poll, so three quiet answers mean it ended before the first poll.
  const PROBE_QUIET_LIMIT = 3

  // Megabytes in the field, bytes in appconfig. The same divisor the template
  // divides by, named on both sides so that the two cannot drift.
  const BYTES_PER_MEGABYTE = 1048576

  // The eight states of the inventory, by the key the template gave their icons.
  // The script shows one of them and hides the rest; it never builds one,
  // because a reason code that became markup here would be the one place on this
  // page where a value from the container turns into an element.
  const CHIP_ICONS = ['indexed', 'truncated', 'queued', 'processing', 'skipped', 'excluded', 'failed', 'unknown']

  let request = null
  // The lookup has a controller of its own, so that it neither aborts the
  // polling nor gets aborted by it: the two calls answer different questions and
  // one of them was asked by a person who is waiting for it.
  let lookupRequest = null
  // And the probe poll has a third, for the same reason: it neither aborts the
  // status poll nor gets aborted by it.
  let probeRequest = null
  // The prefixes as they are stored, which is what makes a prefix NEW. Taken
  // from the server rendered list once, before anything can be edited, and
  // replaced out of the answer of a save. Reading it off the list at comparison
  // time would compare the list with itself and never find anything new.
  let inForcePrefixes = []
  let timer = null
  let unchanged = 0
  let signature = ''

  /**
   * The first numbers, without a round trip.
   *
   * Nextcloud renders one hidden input per key, with the id below and the JSON
   * base64 encoded in its value. atob is safe here although it yields bytes
   * rather than UTF-8: provideInitialState() encodes with json_encode() and
   * without the unescaped unicode flag, so every non ASCII character arrives
   * as an escape sequence and the payload is plain ASCII. It is also only ever
   * numbers, booleans and reason codes, because every label of this page is
   * translated in the template.
   */
  function initialState (key) {
    const element = document.getElementById('initial-state-findling-' + key)
    if (element === null) {
      return null
    }
    try {
      return JSON.parse(atob(element.value))
    } catch (error) {
      return null
    }
  }

  /**
   * The locale of the current session, in the notation Intl expects.
   *
   * Read off the root element rather than through the helpers of OC that ask
   * for the same thing: those two are deprecated, and this attribute is where
   * the layout puts the value they would have returned.
   */
  function locale () {
    const root = document.documentElement
    const own = (root.dataset.locale || '').replace('_', '-')
    return own || root.lang || 'en'
  }

  const numbers = new Intl.NumberFormat(locale())
  const relative = new Intl.RelativeTimeFormat(locale(), { numeric: 'auto' })

  /**
   * A duration as one grain, the same three grains the template uses, so that
   * the sentence does not change its shape when the first poll arrives.
   */
  function span (seconds) {
    if (seconds >= SECONDS_PER_DAY) {
      return n('findling', '%n day', '%n days', Math.floor(seconds / SECONDS_PER_DAY))
    }
    if (seconds >= SECONDS_PER_HOUR) {
      return n('findling', '%n hour', '%n hours', Math.floor(seconds / SECONDS_PER_HOUR))
    }
    return n('findling', '%n minute', '%n minutes', Math.max(1, Math.floor(seconds / SECONDS_PER_MINUTE)))
  }

  /**
   * A size with its unit, in the notation of this session.
   *
   * The same steps the template takes, down to the number of decimals: whole
   * bytes and whole kilobytes, one decimal from megabytes upwards. Both halves
   * of the page have to agree on what one and a half gigabytes looks like,
   * because the template writes the first value and this writes every one
   * after it.
   */
  function size (bytes) {
    let value = Math.max(0, Number.isFinite(bytes) ? bytes : 0)
    let unit = 0
    while (value >= BYTES_PER_UNIT && unit < SIZE_UNITS.length - 1) {
      value /= BYTES_PER_UNIT
      unit++
    }
    const digits = unit < 2 ? 0 : 1
    const formatted = new Intl.NumberFormat(locale(), {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits
    }).format(value)

    return formatted + ' ' + SIZE_UNITS[unit]
  }

  /** The same duration as a point in the past, for the sentence that needs one. */
  function ago (seconds) {
    if (seconds >= SECONDS_PER_DAY) {
      return relative.format(-Math.floor(seconds / SECONDS_PER_DAY), 'day')
    }
    if (seconds >= SECONDS_PER_HOUR) {
      return relative.format(-Math.floor(seconds / SECONDS_PER_HOUR), 'hour')
    }
    return relative.format(-Math.max(1, Math.floor(seconds / SECONDS_PER_MINUTE)), 'minute')
  }

  /**
   * One reading call against one of the two addresses of this page.
   *
   * The token is read out of the document on every single call and never
   * copied into a variable at load time. Nextcloud rotates it when the session
   * is renewed, and a stale copy does not produce an error message: the page
   * simply stops updating and keeps showing yesterday's numbers.
   *
   * The abort signal comes in from the caller rather than being made here. The
   * polling and the single file lookup have one controller each, so that the
   * lookup of a waiting person is never cancelled by the timer and the timer is
   * never cancelled by the lookup.
   */
  async function ask (path, params, signal) {
    const query = params ? '?' + new URLSearchParams(params).toString() : ''
    const url = OC.generateUrl('/apps/findling/' + path) + query

    const response = await fetch(url, {
      signal: signal,
      headers: {
        requesttoken: document.head.dataset.requesttoken,
        Accept: 'application/json'
      }
    })
    if (!response.ok) {
      throw new Error('findling: ' + response.status)
    }

    return response.json()
  }

  /**
   * The one writing call of this page.
   *
   * Separate from ask() and not a parameter on it, because the two differ in
   * more than the verb: this one carries a body, it is triggered by a person
   * pressing a button rather than by a timer, and it is the only call on this
   * page that changes anything. Folding them together would put the writing
   * path one wrong argument away from the polling path.
   *
   * The token is read out of the document inside this function for the same
   * reason as in ask(): Nextcloud rotates it when the session is renewed, and a
   * copy taken at load time fails without an error message after a long
   * session.
   *
   * A non ok answer is returned rather than thrown, because its body carries
   * the field errors and those are the whole point of the answer.
   */
  async function send (path, payload) {
    const response = await fetch(OC.generateUrl('/apps/findling/' + path), {
      method: 'POST',
      headers: {
        requesttoken: document.head.dataset.requesttoken,
        'Content-Type': 'application/json',
        Accept: 'application/json'
      },
      body: JSON.stringify(payload)
    })

    return { ok: response.ok, body: await response.json() }
  }

  function text (id, value) {
    const element = document.getElementById(id)
    if (element !== null) {
      // Text nodes only. The markup of this page belongs to the template, and
      // replacing it from here would mean two places that decide what a tile
      // looks like.
      element.textContent = value
    }
  }

  function shown (id, visible) {
    const element = document.getElementById(id)
    if (element !== null) {
      element.hidden = !visible
    }
  }

  function whole (value) {
    return Number.isInteger(value) && value >= 0 ? value : 0
  }

  function runStateText (view) {
    switch (view.runState) {
      case 'running':
        return t('findling', 'Indexing is running.')
      case 'idle':
        return t('findling', 'Up to date, last checked %s').replace('%s', ago(whole(view.stalledFor)))
      case 'stalled':
        // Word for word the sentence of the template, and both halves are named
        // for the reason written down there (DI-05-22).
        return t('findling', 'Indexing has not progressed for %s. Neither a background job nor the backend finished anything in that time.')
          .replace('%s', span(whole(view.stalledFor)))
      default:
        return t('findling', 'No background job of this app has run yet. Background jobs may not be running.')
    }
  }

  /** The reason groups of the error list as one line, for the fingerprint. */
  function errorSignature (view) {
    const groups = (view.errors || {}).groups
    if (!Array.isArray(groups)) {
      return ''
    }
    return groups.map(function (group) {
      return group.state + ':' + group.reason + ':' + group.count
    }).join(',')
  }

  /** Everything that is allowed to change while the page is open, in one line. */
  function fingerprint (view) {
    const coverage = view.coverage || {}
    const estimate = view.estimate || {}
    const lockstep = view.lockstep || {}
    return [
      lockstep.state, lockstep.container,
      view.runState, view.backendReachable, view.indexedDisplay, view.skipped,
      view.failed, view.excluded, view.scheduled, view.running, view.lastJobRun,
      coverage.indexed, coverage.indexable, coverage.deliberatelyLeftOut,
      coverage.percent, coverage.recounting,
      // The second track belongs in this line or the page stops moving during
      // the one pass it exists to show: while the embedding runs, the full text
      // half stands still, so every other value in here is unchanged from poll
      // to poll and the render would be skipped (D-16).
      coverage.embedded, coverage.embeddedPercent,
      // And the state of the engine behind that figure, for the same reason:
      // it changes on the poll where the first load succeeds or fails, and
      // during that pass nothing else in this line moves at all.
      (view.backend || {}).engineState,
      // The model line of plan 25-04: the precision and whether the vectors
      // are computed again. A run that starts or ends moves nothing else here.
      (view.backend || {}).precisionActive, (view.backend || {}).reembedRunning,
      coverage.provisional, coverage.mountsFinished,
      coverage.mountsTotal, estimate.ocrMeasured, estimate.secondsLeft,
      estimate.bytesExpected, estimate.startupValues, estimate.spaceWarning,
      estimate.firstIndexDone, errorSignature(view)
    ].join('|')
  }

  /**
   * The coverage block, all three of its shapes.
   *
   * Every element is in the template already and the two shapes that do not
   * apply carry the hidden attribute, so this function writes text and flips
   * visibility and never builds markup. The text is written before the
   * visibility so that an element which becomes visible is already correct on
   * the frame it appears in.
   *
   * The figure itself is deliberately not a live region. It changes on every
   * poll, and a screen reader that reads it out every five seconds would make
   * the page unusable for the person it is meant to help. The status line below
   * is the live region, and it changes when something actually happened.
   */
  function coverageBlock (view) {
    const coverage = view.coverage || {}
    const indexable = whole(coverage.indexable)
    const searchable = whole(coverage.indexed)
    // Null and not zero when there is no honest percentage: nought is a claim
    // and null is the absence of one. The template holds a sentence for each of
    // the two cases and neither of them is a number.
    const percent = Number.isInteger(coverage.percent) ? coverage.percent : null
    const hasDenominator = indexable > 0
    const hasFraction = hasDenominator && percent !== null
    // More searchable than indexable: the recount of the denominator has not
    // caught up yet (quick task 260929-kii). Neither a share nor a fraction
    // with a numerator above its denominator, and not the sentence about a
    // silent backend either, but a sentence of its own.
    const recounting = hasDenominator && coverage.recounting === true

    // The separator between the figure and the sign is U+00A0, and it is
    // spelled as an escape rather than as the character itself (IN-03). The
    // template writes the same one, so the number does not change its shape
    // when the script takes over on the first poll. It was written here as a
    // literal before, which reads as an ordinary space in most editors, and
    // the phase 4 review filed the pair as a drift for exactly that reason:
    // the agreement was real and invisible. Non-breaking is the right one of
    // the two, because a percent sign must not wrap away from its number, and
    // whoever changes it here changes it in the template in the same commit.
    text('findling-coverage-percent', numbers.format(percent === null ? 0 : percent) + '\u00a0%')
    text('findling-coverage-subline', t('findling', '%1$s of %2$s indexable files are searchable')
      .replace('%1$s', numbers.format(searchable))
      .replace('%2$s', numbers.format(indexable)))
    text('findling-coverage-recounting', t('findling', '%s files are searchable. Files were added since the last count, so the share is shown again once they have been counted.')
      .replace('%s', numbers.format(searchable)))
    text('findling-coverage-unknown', t('findling', 'The share cannot be worked out right now because the backend does not answer. %s files of this instance are indexable.')
      .replace('%s', numbers.format(indexable)))
    text('findling-coverage-leftout-count', t('findling', 'Deliberately left out: %s')
      .replace('%s', numbers.format(whole(coverage.deliberatelyLeftOut))))
    text('findling-coverage-provisional', t('findling', 'Provisional figure, %1$s of %2$s storages have been counted through.')
      .replace('%1$s', numbers.format(whole(coverage.mountsFinished)))
      .replace('%2$s', numbers.format(whole(coverage.mountsTotal))))

    const bar = document.getElementById('findling-coverage-bar')
    if (bar !== null) {
      bar.setAttribute('value', String(percent === null ? 0 : percent))
    }

    shown('findling-coverage-figure', hasFraction)
    shown('findling-coverage-bar', hasFraction)
    shown('findling-coverage-subline', hasFraction)
    shown('findling-coverage-recounting', recounting)
    shown('findling-coverage-unknown', hasDenominator && !hasFraction && coverage.recounting !== true)
    shown('findling-coverage-leftout', hasDenominator)
    shown('findling-coverage-provisional', hasDenominator && coverage.provisional === true)
    shown('findling-coverage-empty', !hasDenominator)

    semanticBlock(coverage, hasDenominator, (view.backend || {}).engineState)
    modelLine(coverage, hasDenominator, view.backend || {})
  }

  /**
   * The model line of plan 25-04 (D-25-08, D-25-13), word for word the one of
   * the template.
   *
   * The name is built on this side out of one of two words and never taken
   * from the container as text (T-25-14); a container older than the contract
   * of plan 25-12 reports no precision, AdminViewService hands over null, and
   * the line stays hidden. While the vectors are computed again the line adds
   * the progress, read from the same two counters as the share line above and
   * written in the same shape as its figure.
   */
  function modelLine (coverage, hasDenominator, backend) {
    const names = { int8: 'e5-small int8', fp32: 'e5-small fp32' }
    const precision = backend.precisionActive
    const name = (precision === 'int8' || precision === 'fp32') ? names[precision] : ''
    const percent = Number.isInteger(coverage.embeddedPercent) ? coverage.embeddedPercent : null
    const running = backend.reembedRunning === true && hasDenominator && percent !== null

    text('findling-semantic-model', running
      ? t('findling', 'Model: %1$s, re-embedding %2$s (%3$s of %4$s)')
        .replace('%1$s', name)
        .replace('%2$s', numbers.format(percent) + '\u00a0%')
        .replace('%3$s', numbers.format(whole(coverage.embedded)))
        .replace('%4$s', numbers.format(whole(coverage.indexable)))
      : t('findling', 'Model: %1$s').replace('%1$s', name))
    shown('findling-semantic-model', name !== '')
  }

  /**
   * The second coverage figure, the one that fills up after the first index.
   *
   * Called from the block above and not from render(), because it reads the
   * same subtree of the same answer and its denominator is the same number. A
   * second reader of coverage would be a second place that decides what
   * "indexable" means.
   *
   * It has to be written on every poll and not only on the first render, and
   * that is the whole reason this function exists: during the embedding pass
   * the full text half stands still and this figure is the only number on the
   * page that moves. A block that were rendered once server side would sit at
   * the value it had when the page was opened, next to a first figure that is
   * live, which is the shape of a page that lies while looking healthy.
   *
   * Its visibility has two sources since bug audit MEDIUM-3 of plan 07-05: a
   * denominator, or a word about the engine. The second one is what makes the
   * engine line visible on a fresh installation, which is where it says the
   * most and where it used to be hidden behind a figure that does not exist
   * yet.
   */
  function semanticBlock (coverage, hasDenominator, engineState) {
    const indexable = whole(coverage.indexable)
    const embedded = whole(coverage.embedded)
    // Null and not zero for the reason the first figure is: nought per cent is
    // a claim about a semantic half nobody could ask, and the template holds a
    // sentence for that case rather than a number.
    const percent = Number.isInteger(coverage.embeddedPercent) ? coverage.embeddedPercent : null
    const hasFraction = hasDenominator && percent !== null
    // The third question of this block, and it is not about a figure. A word
    // about the engine is enough to show the block, because the line that word
    // becomes says the most on the installation that has no denominator yet
    // (bug audit MEDIUM-3 of plan 07-05). AdminViewService hands over null for
    // a container that did not say, and null is not a word.
    const hasEngineWord = typeof engineState === 'string' && engineState !== ''

    text('findling-semantic-percent', numbers.format(percent === null ? 0 : percent) + '\u00a0%')
    text('findling-semantic-subline', t('findling', '%1$s of %2$s indexable files can also be found by meaning')
      .replace('%1$s', numbers.format(embedded))
      .replace('%2$s', numbers.format(indexable)))

    const bar = document.getElementById('findling-semantic-bar')
    if (bar !== null) {
      bar.setAttribute('value', String(percent === null ? 0 : percent))
    }

    text('findling-semantic-engine', engineSentence(engineState))

    shown('findling-semantic', hasDenominator || hasEngineWord)
    shown('findling-semantic-figure', hasFraction)
    shown('findling-semantic-bar', hasFraction)
    shown('findling-semantic-subline', hasFraction)
    // The denominator belongs in this rule as well, exactly as it does in the
    // first block: a block that appeared for the engine line alone must not
    // claim that a share could not be worked out. There is nothing to work out
    // yet, and the empty block below says so in its own words. While the
    // recount has not caught up, the sentence of the first block says why no
    // share is shown, and "cannot be worked out" would be the wrong reason.
    shown('findling-semantic-unknown', hasDenominator && !hasFraction && coverage.recounting !== true)
  }

  /**
   * The seven sentences about the state of the engine, one of them always right.
   *
   * Word for word the seven of the template, which renders this line server side
   * on the first paint. The two halves have to agree or the sentence changes
   * three seconds after the page opened with nothing having happened, and a
   * gate in backend/tests/test_admin_ui_contract.py holds them together.
   *
   * The container sends one of six words and never a sentence, so nothing an
   * admin reads here comes from across the boundary: the mapping from a word to
   * a sentence lives on this side, in the language of the admin.
   */
  function engineSentence (state) {
    switch (state) {
      case 'loaded':
        return t('findling', 'The model is in memory, the semantic search is answering.')
      case 'cold':
        return t('findling', 'The model is read when it is first needed. That is the normal state.')
      case 'disabled':
        return t('findling', 'The semantic half is switched off in the settings of the container.')
      case 'missing':
        return t('findling', 'There is no model in this image. The search keeps answering with full text hits, the semantic half stays empty.')
      case 'waiting_for_retry':
        return t('findling', 'Reading the model failed once and is tried again shortly. Until then the search answers with full text hits.')
      case 'unloaded':
        return t('findling', 'The model was released to save memory. The next search answers with full text hits and loads it again in the background.')
      default:
        // Everything that is not one of the six, which is what a container
        // older than this app looks like: it sends no state at all and
        // AdminViewService turns that into null. A companion app older than
        // the container lands here too, on the word it does not know yet.
        // Saying "cold" here would promise a load that nobody announced
        // (T-07-03).
        return t('findling', 'This container does not report the state of the model yet.')
    }
  }

  /**
   * Block two, the estimate of the first index.
   *
   * Every element is in the template already, so this writes text and flips
   * visibility and never builds markup. The whole block disappears the moment
   * the first index is through, because an advance estimate has nothing left to
   * say afterwards and the page must not have to be reloaded to stop showing
   * one. It is deliberately not a live region: the three live regions of this
   * page are the status line, the diagnosis card and the save feedback, and a
   * screen reader that read an estimate out every five seconds would be
   * unusable for the person it is meant to help.
   *
   * Null and not zero for the three figures that may not exist yet. A duration
   * of nought reads as "done" and a space requirement of nought reads as
   * "free", so neither is rendered as a number: the sentences the template
   * holds for those cases say what is actually known.
   */
  function estimateBlock (view) {
    const estimate = view.estimate || {}
    const done = estimate.firstIndexDone === true

    shown('findling-estimate', !done)
    if (done) {
      return
    }

    const measured = Number.isInteger(estimate.ocrMeasured) ? estimate.ocrMeasured : null
    const seconds = Number.isInteger(estimate.secondsLeft) ? estimate.secondsLeft : null
    const bytes = Number.isInteger(estimate.bytesExpected) ? estimate.bytesExpected : null
    // Nothing counted yet means no sentence about files at all. A line reading
    // "0 files, 0 to 0 of them need OCR" is the placeholder figure the design
    // contract forbids here, and the counting hint is the whole answer.
    const hasFiles = whole(estimate.files) > 0
    const complete = hasFiles && seconds !== null && bytes !== null
    // An interval while nothing better is known, a single figure once the run
    // has measured one. A single guessed percentage would be a number without
    // a basis.
    const share = measured === null
      ? t('findling', '%1$s to %2$s')
        .replace('%1$s', numbers.format(whole(estimate.ocrMin)))
        .replace('%2$s', numbers.format(whole(estimate.ocrMax)))
      : numbers.format(measured)

    text('findling-estimate-line', t('findling', '%1$s files, %2$s of them need OCR. About %3$s and about %4$s of index.')
      .replace('%1$s', numbers.format(whole(estimate.files)))
      .replace('%2$s', share)
      .replace('%3$s', span(seconds === null ? 0 : seconds))
      .replace('%4$s', size(bytes === null ? 0 : bytes)))
    text('findling-estimate-line-short', t('findling', '%1$s files, %2$s of them need OCR.')
      .replace('%1$s', numbers.format(whole(estimate.files)))
      .replace('%2$s', share))
    text('findling-estimate-counting-text', t('findling', 'Counting the files, this takes a moment.') + ' ' +
      t('findling', 'Provisional figure, %1$s of %2$s storages have been counted through.')
        .replace('%1$s', numbers.format(whole(estimate.mountsFinished)))
        .replace('%2$s', numbers.format(whole(estimate.mountsTotal))))

    shown('findling-estimate-line', complete)
    shown('findling-estimate-line-short', hasFiles && !complete)
    shown('findling-estimate-counting', estimate.provisional === true)
    shown('findling-estimate-space-unknown', hasFiles && bytes === null)
    // Only where there is a duration to label. The flag is true as well while
    // nothing has been measured at all, and labelling an absent figure as a
    // startup value would be a sentence about nothing.
    shown('findling-estimate-startup', estimate.startupValues === true && seconds !== null)
    shown('findling-estimate-space-warning', estimate.spaceWarning === true)
  }

  /**
   * Block three, the error list, and only its numbers.
   *
   * The example paths are deliberately not rebuilt on a poll. They are markup
   * with a focusable button per line, and replacing them every five seconds
   * would throw away the open groups and the keyboard focus of whoever is
   * reading them. So a group whose count changes shows the new count and keeps
   * the examples it has; the next full page load renders the new ones. A group
   * that did not exist at render time has no row to write into either, and it
   * appears with the next load for the same reason.
   */
  function errorsBlock (view) {
    const groups = (view.errors || {}).groups
    if (!Array.isArray(groups)) {
      return
    }
    groups.forEach(function (group) {
      // Keyed by state AND reason, same as the ids the template mints (review
      // finding WR-02): a reason alone would write the count of one state into
      // the row of another the day one code shows up under two states.
      text('findling-errors-count-' + group.state + '-' + group.reason, numbers.format(whole(group.count)))
    })
  }

  /**
   * The expand buttons of the error groups, wired once.
   *
   * The template renders every group open and every button hidden, so the page
   * without this script shows all example paths and offers no control that
   * could not do anything. This function is the moment the control becomes
   * real: it collapses the groups, shows the buttons and keeps aria-expanded
   * and the hidden attribute of the region saying the same thing. Plain showing
   * and hiding, no height animation and no request: the examples are already in
   * the markup.
   */
  function setupErrorGroups () {
    const buttons = document.querySelectorAll('#findling-errors button[aria-controls]')
    Array.prototype.forEach.call(buttons, function (button) {
      const region = document.getElementById(button.getAttribute('aria-controls'))
      if (region === null) {
        return
      }

      region.hidden = true
      button.setAttribute('aria-expanded', 'false')
      button.textContent = t('findling', 'Show example paths')
      button.hidden = false

      button.addEventListener('click', function () {
        const open = button.getAttribute('aria-expanded') === 'true'
        button.setAttribute('aria-expanded', open ? 'false' : 'true')
        region.hidden = open
        button.textContent = open
          ? t('findling', 'Show example paths')
          : t('findling', 'Hide example paths')
      })
    })
  }

  /**
   * Which of the eight chips of the state inventory this answer wears.
   *
   * A file nobody found wears the neutral one, because "there is no such file"
   * is an answer and not a defect: the design contract forbids the error colours
   * for it in as many words. Two reason codes are a state of their own, a
   * truncated document and an excluded file, so both get their own chip instead
   * of reading as a fault under a plain label. Everything this version does not
   * know, ``pending_crawl`` included, ends on the neutral chip, which is exactly
   * what "not seen yet" is.
   */
  function chipOf (view) {
    if (view.found !== true) {
      return 'unknown'
    }
    switch (view.state) {
      case 'indexed':
        return view.reason === 'truncated' ? 'truncated' : 'indexed'
      case 'queued':
        return 'queued'
      case 'processing':
        return 'processing'
      case 'excluded':
        return 'excluded'
      case 'skipped':
        return view.reason === 'excluded' ? 'excluded' : 'skipped'
      case 'failed':
        return 'failed'
      default:
        return 'unknown'
    }
  }

  /** The word beside the icon, so colour is never the only carrier. */
  function chipLabel (chip, view) {
    if (view.found !== true) {
      return t('findling', 'No file at this path, and no file with this ID.')
    }
    switch (chip) {
      case 'indexed':
        return t('findling', 'Indexed')
      case 'truncated':
        return t('findling', 'Indexed, text truncated')
      case 'queued':
        return t('findling', 'Waiting in the queue')
      case 'processing':
        return t('findling', 'Being processed')
      case 'skipped':
        return t('findling', 'Skipped')
      case 'excluded':
        return t('findling', 'Excluded')
      case 'failed':
        return t('findling', 'Failed')
      default:
        // Two states share the neutral chip and may not share a sentence
        // (review finding WR-05). pending_crawl is the honest "the crawl has
        // not arrived", so it keeps "Not seen yet". unknown means the backend
        // is silent and nothing can be said either way, and "Not seen yet"
        // there would be a positive claim about the crawl that the page
        // cannot back; the note underneath names the silent backend, this
        // label says only what holds.
        return view.state === 'unknown'
          ? t('findling', 'State unknown right now')
          : t('findling', 'Not seen yet')
    }
  }

  /**
   * The result card of one lookup, in the order the design contract fixes:
   * state chip, resolved path, reason label, remedy, file id, last checked.
   *
   * Every element is in the template already and every icon of the inventory
   * with it, so this shows one and hides the others and writes text nodes. A new
   * lookup replaces the card; there is no history and no stack, because a stack
   * of answers about different files is a page an administrator has to read
   * bottom up to find the one they just asked for.
   *
   * A row with nothing in it is hidden rather than left empty. An empty line in
   * a diagnostic card is indistinguishable from a defect of the page, which is
   * the same reason the remedy of every reason code says "none" out loud instead
   * of being blank.
   */
  function diagnosisCard (view) {
    const chip = chipOf(view)
    const found = view.found === true
    const fileId = whole(view.fileId)
    const checkedAt = whole(view.checkedAt)
    const path = typeof view.path === 'string' ? view.path : ''
    // The card prints the reference the lookup takes back, and it prints it
    // as the server built it (issue #14, review). Putting uid/files/ in front
    // of the path here doubled it for every file outside the files folder,
    // whose path already starts with the user. The bare path stands in only
    // for an answer without a reference.
    const reference = typeof view.reference === 'string' && view.reference !== ''
      ? view.reference
      : path
    const label = typeof view.label === 'string' ? view.label : ''
    const remedy = typeof view.remedy === 'string' ? view.remedy : ''
    const note = typeof view.note === 'string' ? view.note : ''

    const box = document.getElementById('findling-diagnosis-chip')
    if (box !== null) {
      box.className = 'findling-chip findling-chip--' + chip
    }
    CHIP_ICONS.forEach(function (name) {
      shown('findling-diagnosis-icon-' + name, name === chip)
    })
    text('findling-diagnosis-chip-label', chipLabel(chip, view))

    // The path travels through a function replacement, never as a plain
    // second argument: a string there is a replacement PATTERN, and $&, $'
    // and friends in a file name would be expanded by String.prototype.replace
    // (review finding WR-04). A function's return value is inserted literally.
    text('findling-diagnosis-path', view.trashed === true
      ? t('findling', '%s (in the trash bin)').replace('%s', function () { return path })
      : reference)
    text('findling-diagnosis-label', label)
    text('findling-diagnosis-remedy', remedy)
    text('findling-diagnosis-note', note)
    text('findling-diagnosis-id', t('findling', 'File ID: %s').replace('%s', String(fileId)))
    text('findling-diagnosis-checked', t('findling', 'Last checked %s').replace('%s', ago(elapsed(checkedAt))))

    shown('findling-diagnosis-path', found && path !== '')
    shown('findling-diagnosis-label', label !== '')
    shown('findling-diagnosis-remedy', remedy !== '')
    shown('findling-diagnosis-note', note !== '')
    shown('findling-diagnosis-id', fileId > 0)
    shown('findling-diagnosis-checked', checkedAt > 0)
    shown('findling-diagnosis-result', true)
  }

  /** Seconds since a point in time, and nought for a time nobody recorded. */
  function elapsed (stamp) {
    if (stamp <= 0) {
      return 0
    }
    return Math.max(0, Math.floor(Date.now() / 1000) - stamp)
  }

  /**
   * Ask about one file and show the answer.
   *
   * The button is disabled while the call is out and carries the core spinner,
   * and the field stays usable: somebody who mistyped a path should be able to
   * correct it without waiting for the answer to the wrong one.
   *
   * A failed request leaves the card as it is and says that the lookup did not
   * work. Replacing the card with an error would throw away the answer about the
   * file that was asked about before, and this request says nothing about that
   * file either way.
   */
  async function lookUpOneFile (reference) {
    const field = document.getElementById('findling-diagnosis-input')
    const button = document.getElementById('findling-diagnosis-submit')
    if (field === null) {
      return
    }

    const value = reference === null ? field.value.trim() : reference.trim()
    if (value === '') {
      field.focus()
      return
    }

    field.value = value
    if (lookupRequest !== null) {
      // The previous answer is about a different file and nobody is waiting for
      // it any more.
      lookupRequest.abort()
    }
    lookupRequest = new AbortController()

    if (button !== null) {
      button.disabled = true
    }
    shown('findling-diagnosis-spinner', true)

    try {
      diagnosisCard(await ask(ROUTE_DIAGNOSE, { ref: value }, lookupRequest.signal))
    } catch (error) {
      if (error.name !== 'AbortError') {
        text('findling-diagnosis-note', t('findling', 'The lookup did not work. Nothing about this file has changed.'))
        shown('findling-diagnosis-note', true)
        shown('findling-diagnosis-result', true)
      }
    } finally {
      lookupRequest = null
      if (button !== null) {
        button.disabled = false
      }
      shown('findling-diagnosis-spinner', false)
    }
  }

  /**
   * The lookup, wired once, and the second half of D-04 with it.
   *
   * Three ways in and they all end in the same call: the button, Enter in the
   * field, which the form gives us without a keyboard handler, and every example
   * path of the error list. The last one is what makes the two blocks one tool
   * rather than two lists: a click fills the field, scrolls the block into view
   * and runs the lookup, so the reason in the card is the reason of the row that
   * was clicked.
   *
   * The sentence about JavaScript is hidden here, at the one moment that proves
   * it wrong.
   */
  function setupDiagnosis () {
    shown('findling-diagnosis-nojs', false)

    const form = document.getElementById('findling-diagnosis-form')
    if (form !== null) {
      form.addEventListener('submit', function (event) {
        // The form has no action, so the default would reload the settings page
        // and lose the answer it is about to show.
        event.preventDefault()
        lookUpOneFile(null)
      })
    }

    const examples = document.querySelectorAll('#findling-errors button[data-findling-path]')
    Array.prototype.forEach.call(examples, function (button) {
      button.addEventListener('click', function () {
        // The path where there is one and the file id where there is none: a row
        // whose file id no longer resolves carries the number and nothing else,
        // and that number is exactly what the lookup can still answer about.
        const reference = button.dataset.findlingPath || button.dataset.findlingFileId || ''
        const block = document.getElementById('findling-diagnosis')
        if (block !== null) {
          block.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }
        lookUpOneFile(reference)
      })
    })
  }

  /**
   * Block five, the four rules, and the one part of this page that writes.
   *
   * Every change is local until "Save rules" is pressed. There is no auto save,
   * because a folder exclusion takes documents out of the index and a control
   * that acts while somebody is still typing is a control that acts on a half
   * typed path.
   *
   * The list can grow, which is the one place on this page where an element has
   * to come into existence at runtime. It is cloned from the template element
   * the PHP template holds, and its two variable parts are a text node and an
   * aria-label. So the rule still holds: this script never assembles markup out
   * of a string, and a folder name can therefore not become an element no
   * matter what characters it contains.
   */
  function currentPrefixes () {
    const list = document.getElementById('findling-rules-list')
    if (list === null) {
      return []
    }
    return Array.prototype.map.call(
      list.querySelectorAll('.findling-rules__prefix'),
      function (span) {
        return span.textContent
      }
    )
  }

  /** Show or hide the "nothing is excluded" sentence, after every change. */
  function refreshEmptyState () {
    shown('findling-rules-exclusions-empty', currentPrefixes().length === 0)
  }

  /** One error at one field, with the focus moved into it. */
  function fieldError (errorId, fieldId, message) {
    text(errorId, message)
    shown(errorId, true)
    const field = document.getElementById(fieldId)
    if (field !== null) {
      field.focus()
    }
  }

  function clearFieldError (errorId) {
    shown(errorId, false)
  }

  /** One row of the exclusion list, cloned from the template of the page. */
  function addPrefixRow (prefix) {
    const list = document.getElementById('findling-rules-list')
    const template = document.getElementById('findling-rules-row')
    if (list === null || template === null) {
      return
    }

    const row = template.content.cloneNode(true)
    const label = row.querySelector('.findling-rules__prefix')
    const remove = row.querySelector('.findling-rules__remove')
    if (label === null || remove === null) {
      return
    }

    label.textContent = prefix
    // A function replacement, because a plain string is a replacement PATTERN
    // and a folder named with $& or $' in it would be mangled (review finding
    // WR-04).
    remove.setAttribute('aria-label', t('findling', 'Remove exclusion %s').replace('%s', function () { return prefix }))
    list.appendChild(row)
  }

  /**
   * Add and remove, both local and neither of them saved.
   *
   * Remove is wired by delegation on the list, so a row that was cloned a
   * moment ago needs no wiring of its own and a row that was rendered by the
   * server needs none either. One handler for both is also one place where the
   * unsaved state is announced.
   */
  function setupExclusionList () {
    const field = document.getElementById('findling-rules-new')
    const add = document.getElementById('findling-rules-add')
    const list = document.getElementById('findling-rules-list')

    if (add !== null && field !== null) {
      add.addEventListener('click', function () {
        const value = field.value.trim()
        if (value === '') {
          fieldError('findling-rules-new-error', 'findling-rules-new', t('findling', 'Enter a folder path.'))
          return
        }
        if (currentPrefixes().indexOf(value) !== -1) {
          fieldError('findling-rules-new-error', 'findling-rules-new', t('findling', 'This path is already excluded.'))
          return
        }

        clearFieldError('findling-rules-new-error')
        addPrefixRow(value)
        field.value = ''
        field.focus()
        refreshEmptyState()
        touched()
      })
    }

    if (list !== null) {
      list.addEventListener('click', function (event) {
        const remove = event.target.closest('.findling-rules__remove')
        if (remove === null) {
          return
        }
        const row = remove.closest('.findling-rules__row')
        if (row !== null) {
          row.remove()
          refreshEmptyState()
          touched()
        }
      })
    }
  }

  /**
   * The effect line, shown while something is unsaved.
   *
   * It is the answer to the question an unsaved form raises, "what happens when
   * I press this", and the answer is the one sentence that matters here: the
   * next run applies it and nothing restarts. The saved feedback goes away at
   * the same moment, because it is about the previous state of the form.
   */
  function touched () {
    shown('findling-rules-effect', true)
    shown('findling-rules-feedback', false)
    // A confirmation is about the list as it stood when it was asked for. The
    // moment somebody changes the form again it is about nothing, so it goes
    // away rather than waiting to be accepted for a list that has moved on.
    hideConfirmation()
  }

  function newExclusionsOf (exclusions) {
    return exclusions.filter(function (prefix) {
      return inForcePrefixes.indexOf(prefix) === -1
    })
  }

  /**
   * The inline confirmation of D-07: name the consequence before it happens.
   *
   * A new exclusion does not only stop new documents from being indexed, it
   * takes the ones already indexed under that path out of the index. That is a
   * loss, so it is confirmed, and it is confirmed with the number of documents
   * and the path in the sentence rather than with "are you sure": a number is
   * something an administrator can weigh, and a question they cannot answer
   * teaches them to click it away.
   *
   * Inline and never a dialog. The core helper for a destructive dialog is
   * deprecated since Nextcloud 30 while this app carries max-version 35, and
   * inline is where the consequence stands anyway, right over the button.
   *
   * True means "save now": the list holds nothing that is new after
   * normalisation, so there is nothing to lose. False means the confirmation is
   * on the screen and the confirming button will come back through saveRules.
   *
   * A failed preview does not block the save and does not invent a number
   * either. The consequence is the same whether or not the count succeeded, so
   * the sentence appears without a figure instead of claiming nought documents,
   * which would be the one wrong thing this box could say.
   */
  async function confirmNewExclusions (exclusions) {
    const box = document.getElementById('findling-rules-confirm')
    const cancel = document.getElementById('findling-rules-confirm-cancel')
    const save = document.getElementById('findling-rules-save')
    if (box === null) {
      return true
    }

    let answer = null
    try {
      answer = await ask(ROUTE_RULES_PREVIEW, exclusions.map(function (prefix) {
        // One pair per entry, because a list travels as repeated parameters and
        // a joined string would arrive as one folder with commas in its name.
        return ['exclusions[]', prefix]
      }))
    } catch (error) {
      answer = null
    }

    const answered = answer !== null && Array.isArray(answer.newPrefixes)
    if (answered && answer.newPrefixes.length === 0) {
      return true
    }

    const prefixes = answered ? answer.newPrefixes : newExclusionsOf(exclusions)
    const counted = answered && Number.isInteger(answer.affectedDocuments)
    const documents = counted
      ? (answer.capped === true
          ? t('findling', 'at least %s').replace('%s', numbers.format(answer.affectedDocuments))
          : numbers.format(answer.affectedDocuments))
      : ''

    // This is the one sentence on the page that must be exact, so both
    // substitutions are function replacements: a plain string is a replacement
    // PATTERN, and a folder named Archiv$&2024 would render mangled inside the
    // destructive confirmation (review finding WR-04). The figure goes in
    // FIRST and the folder names LAST, because a function only guards the
    // dollar patterns of its own insertion: a prefix containing the literal
    // text of the other placeholder must not be there any more when the later
    // replace scans the sentence, and the figure cannot contain a placeholder.
    text(
      'findling-rules-confirm-message',
      counted
        ? t('findling', 'Remove indexed content? Excluding %1$s also removes %2$s already indexed documents under that path from the index. The files themselves stay untouched on disk.')
          .replace('%2$s', function () { return documents })
          .replace('%1$s', function () { return prefixes.join(', ') })
        : t('findling', 'Remove indexed content? Excluding %s also removes the documents already indexed under that path from the index. The files themselves stay untouched on disk.')
          .replace('%s', function () { return prefixes.join(', ') })
    )

    shown('findling-rules-confirm', true)
    if (save !== null) {
      // Disabled while the box stands, so the only way past it is one of its
      // own two buttons.
      save.disabled = true
    }
    if (cancel !== null) {
      // The focus goes to the harmless choice. Somebody who presses the space
      // bar without reading keeps their files indexed.
      cancel.focus()
    }

    return false
  }

  /** Take the confirmation off the screen and give the button back. */
  function hideConfirmation () {
    shown('findling-rules-confirm', false)
    const save = document.getElementById('findling-rules-save')
    if (save !== null) {
      save.disabled = false
    }
  }

  /**
   * Discard the confirmation: nothing is written, the list stays as it is.
   *
   * The focus goes back to the button that opened the box, because the element
   * it currently sits on is about to be hidden and a hidden element with the
   * focus leaves a keyboard user nowhere.
   */
  function dismissConfirmation () {
    hideConfirmation()
    const save = document.getElementById('findling-rules-save')
    if (save !== null) {
      save.focus()
    }
  }

  /**
   * Validate, then write, then say what happened.
   *
   * The cap is judged here as well as on the server, and the two are not
   * redundant: this one puts the message at the field with the focus in it,
   * which is what the interaction contract asks for, and the server one is the
   * boundary. The server also clamps, so the answer carries the value in force
   * and the field is set to it afterwards: a value silently lowered would be a
   * page showing a limit that does not hold.
   *
   * Called twice for one save when the list holds a new exclusion: once from
   * the button, which ends in the confirmation, and once from the confirming
   * button with ``confirmed`` true. The second call validates everything again
   * rather than carrying values along, because the form is still editable while
   * the box stands and the values that get written have to be the ones on the
   * screen at the moment of the write.
   *
   * A change that adds no exclusion writes without a confirmation. Moving the
   * cap or flipping a switch takes nothing out of the index, so there is nothing
   * to lose and nothing to confirm.
   */
  async function saveRules (confirmed) {
    const cap = document.getElementById('findling-rules-cap')
    const button = document.getElementById('findling-rules-save')
    if (cap === null) {
      return
    }

    const ceiling = Number(cap.getAttribute('max')) || 1
    const megabytes = Number.parseInt(cap.value, 10)
    if (!Number.isInteger(megabytes) || megabytes < 1 || megabytes > ceiling) {
      fieldError(
        'findling-rules-cap-error',
        'findling-rules-cap',
        t('findling', 'Enter a size between %1$s and %2$s MB.')
          .replace('%1$s', numbers.format(1))
          .replace('%2$s', numbers.format(ceiling))
      )
      return
    }
    clearFieldError('findling-rules-cap-error')
    clearFieldError('findling-rules-new-error')

    const exclusions = currentPrefixes()
    if (confirmed !== true && newExclusionsOf(exclusions).length > 0) {
      const proceed = await confirmNewExclusions(exclusions)
      if (!proceed) {
        return
      }
    }

    hideConfirmation()

    if (button !== null) {
      button.disabled = true
    }

    try {
      const answer = await send(ROUTE_RULES, {
        exclusions: exclusions,
        maxFileBytes: megabytes * BYTES_PER_MEGABYTE,
        indexTeamFolders: checked('findling-rules-team-folders'),
        indexExternalStorage: checked('findling-rules-external-storage')
      })

      if (answer.ok && answer.body.saved === true) {
        applyRules(answer.body.rules)
        feedback(true, t('findling', 'Rules saved. The next run applies them.'))
        shown('findling-rules-effect', false)
        return
      }

      // "Nothing changed" is the payload of this message. The route writes all
      // four values or none of them, so an administrator does not have to work
      // out which half held.
      feedback(false, t('findling', 'The rules were not saved. Nothing changed.'))
    } catch (error) {
      feedback(false, t('findling', 'The rules were not saved. Nothing changed.'))
    } finally {
      if (button !== null) {
        button.disabled = false
      }
    }
  }

  function checked (id) {
    const box = document.getElementById(id)
    return box !== null && box.checked === true
  }

  /** The answer of a save, inline and never a toast. */
  function feedback (success, message) {
    const box = document.getElementById('findling-rules-feedback')
    if (box === null) {
      return
    }
    box.className = 'findling-rules__feedback findling-rules__feedback--' + (success ? 'success' : 'error')
    box.textContent = message
    box.hidden = false
  }

  /**
   * The rules as they are in force after a save.
   *
   * Written back into the form because the server clamps the cap at what the
   * container reported, so the number that holds is not always the number that
   * was typed. Showing the typed one would be this page claiming a limit the
   * container ignores, one screen further along than the contradiction this
   * phase exists to remove.
   */
  function applyRules (rules) {
    if (rules === null || typeof rules !== 'object') {
      return
    }

    const cap = document.getElementById('findling-rules-cap')
    if (cap !== null && Number.isInteger(rules.maxFileBytes)) {
      cap.value = String(Math.max(1, Math.floor(rules.maxFileBytes / BYTES_PER_MEGABYTE)))
    }
    if (cap !== null && Number.isInteger(rules.maxFileBytesCeiling)) {
      cap.setAttribute('max', String(Math.max(1, Math.floor(rules.maxFileBytesCeiling / BYTES_PER_MEGABYTE))))
    }

    const list = document.getElementById('findling-rules-list')
    if (list !== null && Array.isArray(rules.exclusions)) {
      // Rebuilt from the answer, because the server normalises: "files/Archiv"
      // and "/Archiv/" are one and the same rule, and the form has to show the
      // spelling that will be compared.
      while (list.firstChild !== null) {
        list.removeChild(list.firstChild)
      }
      rules.exclusions.forEach(function (prefix) {
        if (typeof prefix === 'string') {
          addPrefixRow(prefix)
        }
      })
      refreshEmptyState()
      // These are the prefixes in force from now on, so the next save measures
      // "new" against them. Without this line the same prefix would ask for a
      // confirmation a second time, for a clearing that already happened.
      inForcePrefixes = currentPrefixes()
    }
  }

  /**
   * The rules block, wired once.
   *
   * The effect line starts hidden here, at the one moment that proves it is
   * about unsaved changes: nothing has been changed yet. Without a script it
   * stays visible, which is the honest reading of a form that cannot be saved
   * without one.
   */
  function setupRules () {
    shown('findling-rules-effect', false)
    refreshEmptyState()
    setupExclusionList()

    // The list as the server rendered it is the list in force. Read before any
    // handler can change it.
    inForcePrefixes = currentPrefixes()

    const save = document.getElementById('findling-rules-save')
    if (save !== null) {
      save.addEventListener('click', function () {
        saveRules()
      })
    }

    const confirmBox = document.getElementById('findling-rules-confirm')
    const accept = document.getElementById('findling-rules-confirm-accept')
    const cancel = document.getElementById('findling-rules-confirm-cancel')

    if (accept !== null) {
      accept.addEventListener('click', function () {
        // The one click that writes a new exclusion, and the only way past the
        // box: the button behind it is disabled while the box stands.
        saveRules(true)
      })
    }

    if (cancel !== null) {
      cancel.addEventListener('click', dismissConfirmation)
    }

    if (confirmBox !== null) {
      confirmBox.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') {
          dismissConfirmation()
        }
      })
    }

    Array.prototype.forEach.call(
      document.querySelectorAll('#findling-rules input'),
      function (field) {
        field.addEventListener('change', touched)
      }
    )
  }

  /*
   * Block "Performance profile" (plan 27-12, UI-01, PRUEF-01).
   *
   * Every state of the block lies in the template (plan 27-10); this part
   * flips the hidden attribute and the disabled flag and writes text nodes,
   * nothing else. Every word comes out of a map below keyed by a code of a
   * closed set, the same catalogue sentence the template map of the same name
   * holds, and a code outside a map leaves its line hidden (T-27-39). The
   * browser decides only the label of the primary button: whether a change
   * needs the probe is decided again by the server, which refuses a way down
   * that is none (T-27-40). The two writing calls carry the profile and the
   * precision and nothing else; the confirmation of the guard is added on the
   * server and never seen here (T-27-41, D-27-12).
   */

  // What the form compares against, out of the overview of the bootstrap and
  // of every status poll.
  const profile = {
    stored: false,
    saved: 'economy',
    suggested: '',
    effective: '',
    precision: 'int8',
    reachable: false,
    supported: false,
    rebuilding: false,
    documents: 0,
    secondsInt8: null,
    secondsFp32: null,
    // Whether the admin changed the form since it was last set from the stored
    // state. An untouched form follows the stored state of the poll, a touched
    // one is left alone.
    touched: false,
    // The probe the page is watching, if any.
    probing: false,
    sawRunning: false,
    quietPolls: 0,
    resultBefore: '',
    lastStep: '',
    lastQuarter: -1,
    timer: null,
    // The sentence of a start that did not happen, until the form changes.
    startError: ''
  }

  const PROFILES = ['economy', 'standard', 'performance']
  const VERDICT_ICONS = ['fits', 'narrow', 'nofit']
  const MODEL_NAMES = { int8: 'e5-small int8', fp32: 'e5-small fp32' }

  /** The three profile names, the catalogue words the template uses. */
  function profileNames () {
    return {
      economy: t('findling', 'Economy'),
      standard: t('findling', 'Standard'),
      performance: t('findling', 'Performance')
    }
  }

  /**
   * The steps of a running probe (probe.STEPS), word for word the map
   * $stepNames of the template. The template leaves out download and ocr_n,
   * because their figures exist only in the answer of the probe route; this
   * side has that answer and names all eight.
   */
  function stepNames () {
    return {
      pause: t('findling', 'waiting for the indexing batch'),
      download: t('findling', 'downloading the model, %1$s of %2$s'),
      digest: t('findling', 'verifying the model file'),
      model: t('findling', 'loading the model'),
      ocr_one: t('findling', 'OCR with one slot'),
      calc: t('findling', 'calculating memory'),
      ocr_n: t('findling', 'OCR with %s slots'),
      cleanup: t('findling', 'cleaning up')
    }
  }

  /** The three verdicts, the map $verdictNames of the template. */
  function verdictNames () {
    return {
      fits: t('findling', 'Fits'),
      narrow: t('findling', 'Fits narrowly'),
      nofit: t('findling', 'Does not fit')
    }
  }

  /** The causes of a verdict (probe.CAUSES), the map $probeCauseNames of the template. */
  function probeCauseNames () {
    return {
      reserve_thin: t('findling', 'Memory reserve too thin: %1$s left, %2$s needed.'),
      memory_short: t('findling', 'Not enough memory: %1$s OCR slots need about %2$s, %3$s are available.'),
      model_memory: t('findling', 'Not enough memory for the fp32 model: it needs about %1$s, %2$s are available.'),
      slot_killed: t('findling', 'A test slot was ended for lack of memory.'),
      timeout: t('findling', 'The measurement took longer than %s.'),
      download_failed: t('findling', 'The model could not be downloaded. Check that github.com and release-assets.githubusercontent.com are reachable.'),
      download_slow: t('findling', 'The download took longer than %s.'),
      digest_mismatch: t('findling', 'The model file does not match its checksum and was deleted.'),
      disk_short: t('findling', 'Not enough disk space for the fp32 model.'),
      memory_unknown: t('findling', 'The available memory could not be read.'),
      interrupted: t('findling', 'The check was interrupted by a restart of the backend.'),
      pause_timeout: t('findling', 'The running indexing batch did not end within %s.'),
      probe_failed: t('findling', 'The check stopped with an error.')
    }
  }

  /**
   * The figures each cause sentence needs, in placeholder order, with the
   * formatter of each, the map $probeCauseNeeds of the template. A sentence
   * with a hole in it is never shown.
   */
  const PROBE_CAUSE_NEEDS = {
    reserve_thin: [['reserve', size], ['required', size]],
    memory_short: [['slots', count], ['need', size], ['available', size]],
    model_memory: [['need', size], ['available', size]],
    timeout: [['seconds', span]],
    download_slow: [['seconds', span]],
    pause_timeout: [['seconds', span]]
  }

  /** Why a start did not happen, by the code of the start route. */
  function startErrors () {
    return {
      busy: t('findling', 'A check is already running. Its result appears here.'),
      unreachable: t('findling', 'The check needs the backend, and it does not answer right now. Nothing was saved.'),
      unsupported: t('findling', 'This backend version cannot run the check. Bring both halves of Findling to the same version.'),
      rebuilding: t('findling', 'The index is being rebuilt right now. The check is possible afterwards.')
    }
  }

  /** The precision verdict of the model line, the map $precisionSentences of the template. */
  function precisionSentences () {
    return {
      fp32_unavailable: t('findling', 'The fp32 model is not available. The search uses int8.'),
      fp32_on_a_tight_box: t('findling', 'fp32 is set, but this box has too little memory for it. The search uses int8.'),
      fp32_not_in_economy: t('findling', 'fp32 is only available in Standard and Performance. The search uses int8.'),
      fp32_active_in_economy: t('findling', 'fp32 stays active under Economy. To go back to int8, choose Standard or Performance and clear the tick.'),
      downloading: t('findling', 'The fp32 model is being downloaded.')
    }
  }

  /** Why the guard lowered the profile, the map $causeNames of the template. */
  function guardCauseNames () {
    return {
      memory_max_repeated: t('findling', 'memory tight, memory.events max twice'),
      oom_kill: t('findling', 'a slot was killed for lack of memory'),
      unclean_end: t('findling', 'the container ended during a multi slot pass')
    }
  }

  function count (value) {
    return numbers.format(value)
  }

  /**
   * The placeholders of a catalogue sentence, filled in one pass.
   *
   * One regular expression with a function replacement, so neither a dollar
   * pattern nor the literal text of another placeholder inside a value can be
   * expanded: every value is inserted once and never scanned again.
   */
  function fill (sentence, values) {
    let next = 0
    return sentence.replace(/%(?:(\d)\$)?s/g, function (match, position) {
      const value = position ? values[Number(position) - 1] : values[next++]
      return value === undefined ? match : String(value)
    })
  }

  function profileCode (value) {
    return typeof value === 'string' && PROFILES.indexOf(value) !== -1 ? value : ''
  }

  function wholeOrNull (value) {
    return Number.isInteger(value) && value >= 0 ? value : null
  }

  /**
   * Whether this change goes through the probe (D-27-09), the rule of
   * SettingsService::needsProbe to the letter. No probe exactly when the target
   * is economy, or when the target is the stored profile and the one change is
   * fp32 to int8. Performance to standard runs through the probe. The server
   * decides again; this only picks the label of the button.
   */
  function needsProbe (target, precision, stored, storedPrecision) {
    if (target === 'economy') {
      return false
    }
    return !(target === stored && storedPrecision === 'fp32' && precision === 'int8')
  }

  function element (id) {
    return document.getElementById(id)
  }

  function disable (id, off) {
    const control = element(id)
    if (control !== null) {
      control.disabled = off
    }
  }

  function focus (id) {
    const target = element(id)
    if (target !== null) {
      target.focus()
    }
  }

  /** One sentence into the one live region of the block. */
  function announce (sentence) {
    text('findling-profile-announce', sentence)
  }

  /** The profile the select shows, or economy for a select that is not there. */
  function formProfile () {
    const select = element('findling-profile-select')
    return select === null ? 'economy' : (profileCode(select.value) || 'economy')
  }

  /**
   * The precision the form leads to. Under economy the tick is hidden and the
   * stored precision stays (D-25-10), so the form cannot ask for a change of
   * precision there.
   */
  function formPrecision () {
    if (formProfile() === 'economy') {
      return profile.precision
    }
    return checked('findling-profile-fp32') ? 'fp32' : 'int8'
  }

  function formChanged () {
    return formProfile() !== profile.saved || formPrecision() !== profile.precision
  }

  /** Whether a probe cannot start right now, and the sentence that says why. */
  function probeBlockedText () {
    const errors = startErrors()
    if (!profile.reachable) {
      return errors.unreachable
    }
    if (!profile.supported) {
      return errors.unsupported
    }
    if (profile.rebuilding) {
      return errors.rebuilding
    }
    return ''
  }

  /** Put the form back on the stored state, or on the suggestion before a first choice (Z1, Z2). */
  function resetForm () {
    const select = element('findling-profile-select')
    const box = element('findling-profile-fp32')
    if (select !== null) {
      select.value = profile.stored ? profile.saved : (profile.suggested || 'economy')
    }
    if (box !== null) {
      box.checked = profile.precision === 'fp32'
    }
    profile.touched = false
  }

  /**
   * The form after every change, every poll and every answer: visibility of
   * the tick, the description, the reindex line, the label and the disabled
   * flag of the buttons (Z1 to Z5, Z14 to Z16a).
   */
  function refreshForm () {
    const target = formProfile()
    const precision = formPrecision()
    const changed = formChanged()
    const probe = needsProbe(target, precision, profile.saved, profile.precision)
    const blocked = probeBlockedText()

    PROFILES.forEach(function (name) {
      shown('findling-profile-describe-' + name, name === target)
    })
    const select = element('findling-profile-select')
    if (select !== null) {
      select.setAttribute('aria-describedby', 'findling-profile-describe-' + target + ' findling-profile-nochange')
    }
    shown('findling-profile-fp32-row', target !== 'economy')
    shown('findling-profile-fp32-help', target !== 'economy')

    // D-27-03, D-27-18: the moment the precision moves, without a dialog; the
    // duration only out of a rate this box measured.
    const seconds = precision === 'fp32' ? profile.secondsFp32 : profile.secondsInt8
    text('findling-profile-reindex-long', fill(
      t('findling', 'Re-embedding of %1$s documents, estimated about %2$s. Full text search stays fully available.'),
      [count(profile.documents), span(seconds === null ? 0 : seconds)]))
    text('findling-profile-reindex-short', fill(
      t('findling', 'Re-embedding of %s documents. Full text search stays fully available.'),
      [count(profile.documents)]))
    shown('findling-profile-reindex-long', seconds !== null)
    shown('findling-profile-reindex-short', seconds === null)
    shown('findling-profile-reindex', precision !== profile.precision)

    const apply = element('findling-profile-apply')
    if (apply !== null) {
      const label = (!changed || probe) ? apply.dataset.labelCheck : apply.dataset.labelApply
      if (typeof label === 'string' && label !== '') {
        apply.textContent = label
      }
      apply.disabled = profile.probing || !changed || (probe && blocked !== '')
    }
    shown('findling-profile-nochange', !changed)
    shown('findling-profile-stay', profile.saved === 'economy' && profile.suggested !== '' && profile.suggested !== 'economy')

    disable('findling-profile-select', profile.probing)
    disable('findling-profile-fp32', profile.probing)
    disable('findling-profile-stay', profile.probing)
    disable('findling-profile-offer-stay', profile.probing)
    // Unreachable, too old or rebuilding locks the probe buttons only; the
    // ways without a probe stay open, because they only write appconfig.
    disable('findling-profile-recheck', profile.probing || blocked !== '')
    disable('findling-profile-offer-check', profile.probing || blocked !== '')

    // During a probe only the sentence of its own start stands (Z16); the
    // reasons a probe cannot start say nothing about the one that runs.
    const error = profile.probing ? profile.startError : (profile.startError !== '' ? profile.startError : blocked)
    text('findling-profile-error', error)
    shown('findling-profile-error', error !== '')
  }

  /** The inline answer of a save without a probe, never a toast. */
  function profileFeedback (success, message) {
    const box = element('findling-profile-feedback')
    if (box === null) {
      return
    }
    box.className = 'findling-rules__feedback findling-rules__feedback--' + (success ? 'success' : 'error')
    box.textContent = message
    box.hidden = false
    announce(message)
  }

  /**
   * Store a way down without a probe (Z5, D-27-09), or economy on "Stay on
   * Economy" even when economy is in force (D-27-11). The focus stays where
   * it is, the live region carries the answer.
   */
  async function saveProfile (target, precision, trigger) {
    shown('findling-profile-feedback', false)
    profile.startError = ''
    disable(trigger, true)

    let saved = false
    try {
      const answer = await send(ROUTE_PROFILE, { profile: target, precision: precision })
      saved = answer.ok && answer.body !== null && answer.body.saved === true
    } catch (error) {
      saved = false
    }

    if (saved) {
      profile.stored = true
      profile.saved = target
      profile.precision = precision
      resetForm()
      profileFeedback(true, fill(t('findling', 'Saved. %s applies from the next indexing round.'), [profileNames()[target]]))
      schedule(0)
    } else {
      // Z17: the form keeps the choice, the button is usable again.
      profileFeedback(false, t('findling', 'The profile was not saved. Nothing changed.'))
    }
    disable(trigger, false)
    refreshForm()
  }

  /** A comparable identity of a stored result, so a new one can be told from the last. */
  function resultKey (result) {
    if (result === null || typeof result !== 'object') {
      return ''
    }
    return [result.at, result.profile, result.precision, result.verdict].join('|')
  }

  /**
   * Z6: every control disabled, the card hidden, the progress line up. From a
   * click the focus goes to the progress line, because the button that had it
   * is disabled now; from a page that opened during a probe it stays put.
   */
  function enterProbe (fromClick, resultBefore) {
    profile.probing = true
    profile.sawRunning = false
    profile.quietPolls = 0
    profile.resultBefore = resultBefore
    profile.lastStep = ''
    profile.lastQuarter = -1
    shown('findling-profile-feedback', false)
    shown('findling-profile-verdict', false)
    shown('findling-profile-progress', true)
    shown('findling-profile-progress-hint', true)
    refreshForm()
    if (fromClick) {
      text('findling-profile-progress-text', t('findling', 'Check running.'))
      focus('findling-profile-progress')
      announce(t('findling', 'Check running.'))
    }
    scheduleProbe(POLL_PROBE_MS)
  }

  function scheduleProbe (delay) {
    window.clearTimeout(profile.timer)
    profile.timer = window.setTimeout(probePoll, delay)
  }

  /**
   * The progress line of one answer. The step is announced when it changes,
   * the download at most every quarter; the line itself is not a live region.
   */
  function progress (answer) {
    const names = stepNames()
    const step = typeof answer.step === 'string' && Object.prototype.hasOwnProperty.call(names, answer.step) ? answer.step : ''
    const done = whole(answer.bytesDone)
    const total = whole(answer.bytesTotal)
    let name = ''
    if (step === 'download') {
      name = total > 0 ? fill(names.download, [size(done), size(total)]) : ''
    } else if (step === 'ocr_n') {
      // ocr_n names the number of slots, carried in numbers.slots; without the
      // figure the line says only that the check runs.
      const slots = whole((answer.numbers || {}).slots)
      name = slots > 0 ? fill(names.ocr_n, [String(slots)]) : ''
    } else if (step !== '') {
      name = names[step]
    }

    const line = name === '' ? t('findling', 'Check running.') : fill(t('findling', 'Check running: %s'), [name])
    text('findling-profile-progress-text', line)

    const quarter = step === 'download' && total > 0 ? Math.min(4, Math.floor((done * 4) / total)) : -1
    if (step !== profile.lastStep || quarter > profile.lastQuarter) {
      announce(line)
    }
    profile.lastStep = step
    profile.lastQuarter = step === 'download' ? Math.max(profile.lastQuarter, quarter) : -1
  }

  async function probePoll () {
    if (probeRequest !== null) {
      probeRequest.abort()
    }
    probeRequest = new AbortController()

    let answer = null
    try {
      answer = await ask(ROUTE_PROFILE_CHECK, null, probeRequest.signal)
    } catch (error) {
      if (error.name === 'AbortError') {
        return
      }
      answer = null
    } finally {
      probeRequest = null
    }

    if (answer === null || answer.code !== 'ok') {
      const errors = startErrors()
      leaveProbe(null, answer !== null && answer.code === 'unsupported' ? errors.unsupported : errors.unreachable)
      return
    }

    if (answer.state === 'running') {
      profile.sawRunning = true
      progress(answer)
      scheduleProbe(POLL_PROBE_MS)
      return
    }

    const result = answer.result !== null && typeof answer.result === 'object' ? answer.result : null
    profile.quietPolls++
    if (profile.sawRunning || resultKey(result) !== profile.resultBefore || profile.quietPolls >= PROBE_QUIET_LIMIT) {
      leaveProbe(result, '')
      return
    }
    scheduleProbe(POLL_PROBE_MS)
  }

  /**
   * The verdict card of one result (Z7 to Z9), out of the same maps as the
   * template. The chip class is one of three fixed words, the rest are text
   * nodes and hidden attributes.
   */
  function verdictCard (result) {
    const names = profileNames()
    const verdicts = verdictNames()
    const verdict = typeof result.verdict === 'string' && Object.prototype.hasOwnProperty.call(verdicts, result.verdict) ? result.verdict : ''
    const target = profileCode(result.profile)
    const precision = result.precision === 'fp32' || result.precision === 'int8' ? result.precision : ''
    if (verdict === '' || target === '' || precision === '') {
      return ''
    }

    const fits = verdict === 'fits'
    const saved = fits && result.committed === true
    const atText = typeof result.atText === 'string' ? result.atText : ''

    const chip = element('findling-profile-verdict-chip')
    if (chip !== null) {
      chip.className = 'findling-chip findling-chip--' + verdict
    }
    VERDICT_ICONS.forEach(function (code) {
      shown('findling-profile-verdict-icon-' + code, code === verdict)
    })
    text('findling-profile-verdict-word', verdicts[verdict])
    text('findling-profile-verdict-checked', fill(t('findling', 'Checked: %1$s with %2$s, %3$s'), [names[target], MODEL_NAMES[precision], atText]))

    const causes = probeCauseNames()
    const cause = !fits && typeof result.cause === 'string' && Object.prototype.hasOwnProperty.call(causes, result.cause) ? result.cause : ''
    const figures = result.numbers !== null && typeof result.numbers === 'object' ? result.numbers : {}
    const values = (PROBE_CAUSE_NEEDS[cause] || []).map(function (need) {
      const value = wholeOrNull(figures[need[0]])
      return value === null ? null : need[1](value)
    })
    const causeLine = cause !== '' && values.indexOf(null) === -1 ? fill(causes[cause], values) : ''
    text('findling-profile-verdict-cause', causeLine)

    const kept = names[profile.effective || profile.saved]
    const savedLine = fill(t('findling', 'Saved. %s applies from the next indexing round.'), [names[target]])
    const keptLine = fill(t('findling', 'Nothing was saved. %s stays in force.'), [kept])
    text('findling-profile-verdict-saved', savedLine)
    text('findling-profile-verdict-kept', keptLine)

    shown('findling-profile-verdict-empty', false)
    shown('findling-profile-verdict-chip', true)
    shown('findling-profile-verdict-checked', atText !== '')
    shown('findling-profile-verdict-cause', causeLine !== '')
    shown('findling-profile-verdict-saved', saved)
    shown('findling-profile-verdict-kept', !saved)
    // D-27-17: only when the probe downloaded the fp32 file itself.
    shown('findling-profile-verdict-deleted', !fits && result.fp32Deleted === true)
    // D-27-08: the next lower step, never "apply anyway".
    shown('findling-profile-offer-check', !fits && target === 'performance')
    shown('findling-profile-offer-stay', !fits && target === 'standard')

    if (saved) {
      profile.stored = true
      profile.saved = target
      profile.precision = precision
    }

    // One sentence for the live region: verdict, cause and consequence.
    return verdicts[verdict] + ': ' + [causeLine, saved ? savedLine : keptLine].filter(function (part) {
      return part !== ''
    }).join(' ')
  }

  /**
   * The end of a probe: the card with the verdict or the error line, the form
   * back on the stored state, the controls usable again, and a status poll
   * straight away so that "In force" follows.
   */
  function leaveProbe (result, error) {
    window.clearTimeout(profile.timer)
    profile.probing = false
    shown('findling-profile-progress', false)
    shown('findling-profile-progress-hint', false)

    const sentence = result === null ? '' : verdictCard(result)
    if (sentence !== '') {
      currentResult = result
    }
    profile.startError = error
    resetForm()
    refreshForm()
    shown('findling-profile-verdict', true)

    if (error !== '') {
      announce(error)
    } else if (sentence !== '') {
      announce(sentence)
    }

    const offer = ['findling-profile-offer-check', 'findling-profile-offer-stay'].filter(function (id) {
      const button = element(id)
      return button !== null && !button.hidden
    })
    if (sentence !== '' && result.verdict !== 'fits' && offer.length > 0) {
      focus(offer[0])
    } else {
      focus('findling-profile-verdict')
    }
    schedule(0)
  }

  /**
   * Start a probe for this target. "started" and "busy" both lead into Z6,
   * the second with its sentence (Z16); every other answer leaves the form as
   * it is and the focus goes back to the button that asked.
   */
  async function startProbe (target, precision, trigger) {
    profile.startError = ''
    shown('findling-profile-feedback', false)
    disable(trigger, true)

    const before = resultKey(currentResult)
    let code = ''
    try {
      const answer = await send(ROUTE_PROFILE_CHECK, { profile: target, precision: precision })
      code = answer.body !== null && typeof answer.body.code === 'string' ? answer.body.code : ''
    } catch (error) {
      code = 'unreachable'
    }

    const errors = startErrors()
    if (code === 'started' || code === 'busy') {
      profile.startError = code === 'busy' ? errors.busy : ''
      enterProbe(true, before)
      if (code === 'busy') {
        announce(errors.busy)
      }
      return
    }

    profile.startError = Object.prototype.hasOwnProperty.call(errors, code) ? errors[code] : ''
    refreshForm()
    if (profile.startError !== '') {
      announce(profile.startError)
    }
    focus(trigger)
  }

  // The stored result of the page as it was rendered, for telling the result
  // of a new probe from the last one.
  let currentResult = null

  /**
   * The facts of the block out of one overview: hardware, suggestion, in
   * force, shrink, guard and precision verdict, each a code turned into a
   * catalogue sentence on this side (Z10, Z11, Z13, Z14, Z15).
   */
  function profileView (view) {
    const names = profileNames()
    const backend = view.backend || {}

    profile.stored = view.profileStored === true
    // The saved profile out of appconfig (profileSaved), never the container's
    // chosen, which lags one round behind a save.
    const saved = profileCode(view.profileSaved)
    profile.saved = profile.stored && saved !== '' ? saved : 'economy'
    // What the container read last; only the shrink line compares it with the
    // profile in force (Z14), the same as the template.
    const chosen = profileCode(view.profileChosen)
    profile.suggested = profileCode(view.profileSuggested)
    profile.effective = profileCode(view.profileEffective)
    profile.precision = view.storedPrecision === 'fp32' ? 'fp32' : 'int8'
    profile.reachable = view.backendReachable === true
    profile.supported = view.probeSupported === true
    profile.rebuilding = backend.rebuildRunning === true
    profile.documents = whole(view.reindexDocuments)
    profile.secondsInt8 = wholeOrNull(view.reindexSecondsInt8)
    profile.secondsFp32 = wholeOrNull(view.reindexSecondsFp32)
    if (view.profileCheck !== undefined) {
      currentResult = view.profileCheck
    }

    const cores = wholeOrNull(view.hardwareCores)
    const memory = wholeOrNull(view.hardwareMemory)
    const known = cores !== null && memory !== null
    if (known) {
      text('findling-profile-hardware', fill(t('findling', 'Detected: cores %1$s, memory %2$s'), [count(cores), size(memory)]))
    }
    shown('findling-profile-hardware', known)
    shown('findling-profile-hardware-unknown', !known)

    if (profile.suggested !== '') {
      text('findling-profile-suggested', fill(t('findling', 'Suggested for this box: %s'), [names[profile.suggested]]))
    }
    shown('findling-profile-suggested', profile.suggested !== '')
    if (profile.effective !== '') {
      text('findling-profile-in-force', fill(t('findling', 'In force: %s'), [names[profile.effective]]))
    }
    shown('findling-profile-in-force', profile.effective !== '')

    const causes = guardCauseNames()
    const guardCause = typeof backend.guardCause === 'string' && Object.prototype.hasOwnProperty.call(causes, backend.guardCause) ? backend.guardCause : ''
    const guardChosen = profileCode(backend.guardChosen)
    const guardEffective = profileCode(backend.guardEffective)
    const guardShown = backend.guardConfirmable === true && guardCause !== '' && guardChosen !== '' && guardEffective !== ''
    if (guardShown) {
      text('findling-profile-guard-text', fill(
        t('findling', 'The memory guard lowered the profile: chosen %1$s, in force %2$s (%3$s).'),
        [names[guardChosen], names[guardEffective], causes[guardCause]]))
    }
    shown('findling-profile-guard', guardShown)

    const shrunk = guardCause === '' && chosen !== '' && profile.effective !== '' && chosen !== profile.effective
    if (shrunk) {
      text('findling-profile-shrunk', fill(
        t('findling', 'Chosen %1$s, in force %2$s: this box has less hardware than the chosen profile needs.'),
        [names[chosen], names[profile.effective]]))
    }
    shown('findling-profile-shrunk', shrunk)

    const sentences = precisionSentences()
    const verdict = typeof backend.precisionVerdict === 'string' && Object.prototype.hasOwnProperty.call(sentences, backend.precisionVerdict)
      ? backend.precisionVerdict
      : ''
    text('findling-profile-precision', verdict === '' ? '' : sentences[verdict])
    shown('findling-profile-precision', verdict !== '')

    if (!profile.touched && !profile.probing) {
      resetForm()
    }
    refreshForm()

    // A probe started in another tab, or before the page was opened (Z6).
    if (view.probeRunning === true && !profile.probing) {
      enterProbe(false, resultKey(currentResult))
    }
  }

  /**
   * The block, wired once. The sentence about JavaScript goes at the one
   * moment that proves it wrong.
   */
  function setupProfile (bootstrap) {
    shown('findling-profile-nojs', false)
    if (element('findling-profile') === null) {
      return
    }

    const select = element('findling-profile-select')
    const box = element('findling-profile-fp32')
    const edited = function () {
      profile.touched = true
      profile.startError = ''
      shown('findling-profile-feedback', false)
      refreshForm()
    }
    if (select !== null) {
      select.addEventListener('change', edited)
    }
    if (box !== null) {
      box.addEventListener('change', edited)
    }

    const apply = element('findling-profile-apply')
    if (apply !== null) {
      apply.addEventListener('click', function () {
        const target = formProfile()
        const precision = formPrecision()
        if (needsProbe(target, precision, profile.saved, profile.precision)) {
          startProbe(target, precision, 'findling-profile-apply')
        } else {
          saveProfile(target, precision, 'findling-profile-apply')
        }
      })
    }

    // "Stay on Economy", in the form and in the card: economy with the stored
    // precision, saved at once and without a probe (D-27-11).
    const stay = function (trigger) {
      return function () {
        if (select !== null) {
          select.value = 'economy'
        }
        if (box !== null) {
          box.checked = false
        }
        saveProfile('economy', profile.precision, trigger)
      }
    }
    const stayButton = element('findling-profile-stay')
    if (stayButton !== null) {
      stayButton.addEventListener('click', stay('findling-profile-stay'))
    }
    const offerStay = element('findling-profile-offer-stay')
    if (offerStay !== null) {
      offerStay.addEventListener('click', stay('findling-profile-offer-stay'))
    }

    // "Check again" of the guard banner: the chosen profile with the stored
    // precision. Only the two values travel (D-27-12).
    const recheck = element('findling-profile-recheck')
    if (recheck !== null) {
      recheck.addEventListener('click', function () {
        startProbe(profile.saved, profile.precision, 'findling-profile-recheck')
      })
    }

    // "Check Standard" of the card after a verdict on Performance.
    const offerCheck = element('findling-profile-offer-check')
    if (offerCheck !== null) {
      offerCheck.addEventListener('click', function () {
        // With the precision the card was about, the next lower step of the
        // same question.
        const last = currentResult !== null && typeof currentResult === 'object' ? currentResult.precision : ''
        startProbe('standard', last === 'fp32' || last === 'int8' ? last : profile.precision, 'findling-profile-offer-check')
      })
    }

    if (bootstrap !== null) {
      profileView(bootstrap)
    } else {
      refreshForm()
    }
  }

  function render (view) {
    text('findling-tile-indexed', numbers.format(whole(view.indexedDisplay)))
    text('findling-tile-skipped', numbers.format(whole(view.skipped)))
    text('findling-tile-failed', numbers.format(whole(view.failed)))
    text('findling-tile-excluded', numbers.format(whole(view.excluded)))
    text('findling-scheduled', numbers.format(whole(view.scheduled)))
    text('findling-running', numbers.format(whole(view.running)))
    shown('findling-processing-chip', whole(view.running) > 0)
    text('findling-run-state', runStateText(view))

    // The percentage is worked out once, on the server, and arrives ready made.
    // Working it out here as well would be a second rule for the same number,
    // and the two would disagree on the day one of them is corrected.
    coverageBlock(view)
    estimateBlock(view)
    errorsBlock(view)

    shown('findling-banner-unreachable', view.backendReachable !== true)

    // The version state of D-11. The sentence is written before the banner is
    // shown, like everywhere else on this page, so that it is already correct on
    // the frame it appears in; and it is written into the text span rather than
    // into the paragraph, which also holds the icon. Both numbers come from the
    // server side comparison and are put into a text node, never into markup.
    const lockstep = view.lockstep || {}
    text('findling-banner-lockstep-text',
      t('findling', 'The two halves of Findling report different versions: this app is %1$s, the backend is %2$s. While they disagree the search answers with no results, because a wrong answer without a word would be worse. Bring both halves to the same version.')
        .replace('%1$s', typeof lockstep.companion === 'string' ? lockstep.companion : '')
        .replace('%2$s', typeof lockstep.container === 'string' ? lockstep.container : ''))
    shown('findling-banner-lockstep', lockstep.state === 'drift')

    const backend = view.backend || {}
    shown('findling-banner-lowdisk', backend.lowDisk === true)
    shown('findling-banner-reindex', backend.reindexRequired === true)

    // The rebuild of plan 18-10, and the sentence is written before the banner
    // is shown, like the version state above: a banner that appears with the
    // figures of the poll before it shows a progress that moved backwards.
    // Written into the text span and never into the paragraph, which holds the
    // icon as well.
    //
    // Both numbers pass through whole() first, so what reaches the sentence is
    // a number and never a value the container put on the wire, and it reaches
    // it through text(), which is a textContent and never markup.
    text('findling-banner-rebuild-text',
      t('findling', 'Findling is rebuilding its index so that the newly switched on languages can be searched. %1$s of %2$s documents have been carried over. Search keeps answering while this runs, and there is nothing to start or to restart.')
        .replace('%1$s', numbers.format(whole(backend.rebuildDone)))
        .replace('%2$s', numbers.format(whole(backend.rebuildTotal))))
    shown('findling-banner-rebuild', backend.rebuildRunning === true)

    // The other outcome of the same run. The figure is the missing amount and
    // it is formatted with the unit table the template uses, so the sentence
    // does not change its shape when the first poll arrives.
    const blockedBytes = whole(backend.rebuildBlockedBytes)
    text('findling-banner-rebuild-space-text',
      t('findling', 'Findling wants to rebuild its index for the newly switched on languages and there is not enough room: %s more are needed next to what the index already uses. Free that much, or set the environment variable FINDLING_REBUILD_FALLBACK=fullreindex to have the backend read the files again instead. Either way the backend only tries again after a restart of the container.')
        .replace('%s', size(blockedBytes)))
    shown('findling-banner-rebuild-space', blockedBytes > 0)

    // The language diagnosis, two lists in one line. Both are strings from the
    // container and both go into a text node.
    const languagesActive = typeof backend.languagesActive === 'string' ? backend.languagesActive : ''
    const languagesFilled = typeof backend.languagesFilled === 'string' ? backend.languagesFilled : ''
    text('findling-languages',
      t('findling', 'Languages of the index: %1$s switched on, %2$s with text in the index.')
        .replace('%1$s', languagesActive)
        .replace('%2$s', languagesFilled))
    shown('findling-languages', languagesActive !== '' || languagesFilled !== '')

    // The facts of the profile block. The form itself is left alone once the
    // admin touched it, for the reason the rules below are not rendered.
    profileView(view)

    // view.rules is deliberately not rendered. Block five is a form somebody may
    // be halfway through filling in, and a poll every five seconds that wrote
    // the stored values back into it would throw away what they just typed. The
    // rules of the answer are read at one moment only: after a save, out of the
    // answer of the save itself, which is the one moment they are known to have
    // changed and the form is known not to be in the middle of anything.
  }

  function cadence (view) {
    const open = whole(view.scheduled) + whole(view.running)
    if (open === 0 || unchanged >= UNCHANGED_LIMIT) {
      return POLL_IDLE_MS
    }
    return POLL_ACTIVE_MS
  }

  function schedule (delay) {
    window.clearTimeout(timer)
    timer = window.setTimeout(poll, delay)
  }

  async function poll () {
    if (document.visibilityState !== 'visible') {
      // Paused rather than slowed down. A forgotten tab must not question the
      // instance for a week, and the listener below picks the page up again the
      // moment it comes back into view.
      return
    }

    // Exactly one polling request in flight. The previous one is abandoned
    // rather than awaited, because its answer is older than the one about to be
    // asked for. The single file lookup has a controller of its own and is not
    // touched here: it was asked by a person who is waiting for it.
    if (request !== null) {
      request.abort()
    }
    request = new AbortController()

    try {
      const view = await ask(ROUTE_OVERVIEW, null, request.signal)
      const current = fingerprint(view)
      unchanged = current === signature ? unchanged + 1 : 0
      signature = current
      render(view)
      shown('findling-banner-stale', false)
      schedule(cadence(view))
    } catch (error) {
      if (error.name === 'AbortError') {
        return
      }
      // The numbers stay exactly as they are. A failed request says nothing
      // about the index, and resetting the tiles to zero would turn a hiccup of
      // this page into the claim that nothing is indexed. The banner says what
      // happened and the polling carries on at the slow cadence.
      shown('findling-banner-stale', true)
      schedule(POLL_IDLE_MS)
    } finally {
      request = null
    }
  }

  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'visible') {
      // Straight away and not at the next tick of the timer: somebody who comes
      // back to this tab is looking at the numbers right now.
      schedule(0)
    } else {
      window.clearTimeout(timer)
    }
  })

  setupErrorGroups()
  setupDiagnosis()
  setupRules()

  const bootstrap = initialState('bootstrap')
  // With the bootstrap, so that a page opened during a probe is in Z6 at once.
  setupProfile(bootstrap)
  if (bootstrap !== null) {
    // Not rendered again, only remembered: the template has already put these
    // very numbers on the page. Remembering them means the first poll can tell
    // whether anything actually changed.
    signature = fingerprint(bootstrap)
    schedule(cadence(bootstrap))
  } else {
    schedule(POLL_ACTIVE_MS)
  }
})()
