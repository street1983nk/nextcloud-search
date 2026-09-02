/**
 * The refresh of block one, in plain browser JavaScript.
 *
 * No module, no bundler, no dependency and no package file anywhere in this
 * app: the page is a PHP template, the Nextcloud server CSS and this file. The
 * script never builds markup. Everything it touches already exists in the
 * template, rendered server side with real values, so the page is complete
 * before this file has run and stays complete if it never runs at all.
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

  let request = null
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
   * One reading call against the one address this page asks.
   *
   * The token is read out of the document on every single call and never
   * copied into a variable at load time. Nextcloud rotates it when the session
   * is renewed, and a stale copy does not produce an error message: the page
   * simply stops updating and keeps showing yesterday's numbers.
   */
  async function ask (path, params) {
    const query = params ? '?' + new URLSearchParams(params).toString() : ''
    const url = OC.generateUrl('/apps/findling/admin/' + path) + query

    request = new AbortController()
    const response = await fetch(url, {
      signal: request.signal,
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

    // Exactly one request in flight. The previous one is abandoned rather than
    // awaited, because its answer is older than the one about to be asked for.
    if (request !== null) {
      request.abort()
    }

    try {
      const view = await ask('overview', null)
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
