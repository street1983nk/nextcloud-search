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

  // The two addresses this page asks, written out whole rather than assembled
  // from a prefix and a name: a grep for either route has to find its caller,
  // and a route that is only half spelled anywhere is a route nobody finds when
  // it moves.
  const ROUTE_OVERVIEW = 'admin/overview'
  const ROUTE_DIAGNOSE = 'admin/diagnose'
  const ROUTE_RULES = 'admin/rules'

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
        return t('findling', 'Indexing has not progressed for %s. Background jobs may not be running.')
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
    return [
      view.runState, view.backendReachable, view.indexedDisplay, view.skipped,
      view.failed, view.excluded, view.scheduled, view.running, view.lastJobRun,
      coverage.indexed, coverage.indexable, coverage.deliberatelyLeftOut,
      coverage.percent, coverage.provisional, coverage.mountsFinished,
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

    text('findling-coverage-percent', numbers.format(percent === null ? 0 : percent) + ' %')
    text('findling-coverage-subline', t('findling', '%1$s of %2$s indexable files are searchable')
      .replace('%1$s', numbers.format(searchable))
      .replace('%2$s', numbers.format(indexable)))
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
    shown('findling-coverage-unknown', hasDenominator && !hasFraction)
    shown('findling-coverage-leftout', hasDenominator)
    shown('findling-coverage-provisional', hasDenominator && coverage.provisional === true)
    shown('findling-coverage-empty', !hasDenominator)
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
      text('findling-errors-count-' + group.reason, numbers.format(whole(group.count)))
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
  function chipLabel (chip, found) {
    if (found !== true) {
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
        return t('findling', 'Not seen yet')
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
    text('findling-diagnosis-chip-label', chipLabel(chip, found))

    text('findling-diagnosis-path', view.trashed === true
      ? t('findling', '%s (in the trash bin)').replace('%s', path)
      : path)
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
    remove.setAttribute('aria-label', t('findling', 'Remove exclusion %s').replace('%s', prefix))
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
  }

  /**
   * The inline confirmation of D-07, and it confirms nothing yet.
   *
   * Plan 04-09 hangs the destructive confirmation in here: a NEW exclusion also
   * removes the documents already indexed under that path from the index, and
   * that consequence has to be confirmed with the number of documents in the
   * sentence. Until that clearing exists there is nothing to lose by saving,
   * and asking somebody to confirm a consequence that does not happen would
   * teach them to click the confirmation away before it ever means anything.
   *
   * It stands here, named and called from its place in the order, rather than
   * being left out: a hook that is incomplete and says so is one somebody can
   * finish, and a missing one is one nobody knows to look for.
   */
  function confirmNewExclusions (exclusions) {
    // The list is in the signature already so that hanging the confirmation in
    // is one function body and not a change at the call site as well: plan
    // 04-09 compares it against what was stored, asks the route how many
    // documents lie under the new prefixes, and returns false until the
    // administrator has pressed the confirming button, saving from there.
    return Array.isArray(exclusions)
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
   */
  async function saveRules () {
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
    if (!confirmNewExclusions(exclusions)) {
      return
    }

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

    const save = document.getElementById('findling-rules-save')
    if (save !== null) {
      save.addEventListener('click', function () {
        saveRules()
      })
    }

    Array.prototype.forEach.call(
      document.querySelectorAll('#findling-rules input'),
      function (field) {
        field.addEventListener('change', touched)
      }
    )
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
    const backend = view.backend || {}
    shown('findling-banner-lowdisk', backend.lowDisk === true)
    shown('findling-banner-reindex', backend.reindexRequired === true)

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
