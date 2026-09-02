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

  /** Everything that is allowed to change while the page is open, in one line. */
  function fingerprint (view) {
    return [
      view.runState, view.backendReachable, view.indexedDisplay, view.skipped,
      view.failed, view.excluded, view.indexable, view.scheduled, view.running,
      view.lastJobRun
    ].join('|')
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

    const indexable = whole(view.indexable)
    const indexed = whole(view.indexedDisplay)
    if (indexable > 0) {
      // Never a hundred while anything is still missing, and never a
      // percentage at all while there is no denominator to name. The template
      // renders the empty state in that case and there is nothing here to fill.
      const percent = indexed >= indexable
        ? 100
        : Math.min(99, Math.max(0, Math.floor(indexed * 100 / indexable)))
      text('findling-coverage-percent', numbers.format(percent) + ' %')
      text('findling-coverage-subline', t('findling', '%1$s of %2$s indexable files are searchable')
        .replace('%1$s', numbers.format(indexed))
        .replace('%2$s', numbers.format(indexable)))
      const bar = document.getElementById('findling-coverage-bar')
      if (bar !== null) {
        bar.value = percent
      }
    }

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
