/**
 * The return marker of the result page, and nothing else.
 *
 * No module, no bundler, no dependency and no package file anywhere in this
 * app: the page is a PHP template, the Nextcloud server CSS and this file. The
 * script never builds markup. Every element it touches already exists in the
 * template, rendered server side with real values, so the page is complete
 * before this file has run and stays complete if it never runs at all. Searching,
 * paging, filtering, opening a hit and coming back all work without it.
 *
 * Why this file is load bearing rather than a courtesy.
 *
 * The design contract assumes that a plain document restores its own scroll
 * position on a backwards navigation, so that the marker is only a nicety. Read
 * against the server sources, that is not what happens here. #app-content is a
 * scroll container of its own, "overflow: auto" inside a "position: fixed"
 * #content, so the document itself never scrolls and the offset the browser
 * would put back is always nought. On top of that every AppFramework answer
 * carries "no-store", which is the classic reason for a page to be kept out of
 * the back forward cache; Firefox names it outright. So this file has two
 * consequences written into it:
 *
 *   - the pageshow handler does not ask whether the page came out of that
 *     cache. In Firefox that question would answer no on every return, and the
 *     marker would never appear.
 *   - scrollIntoView on the row is the actual carrier of the position, because
 *     it scrolls the nearest scrollable ancestor and that ancestor is
 *     #app-content.
 *
 * Two events, and only two. A click on a hit row writes down which row it was;
 * the click itself is not intercepted, so the link follows normally, in the same
 * tab, and a middle click still opens a new one. A pageshow reads the note back.
 * Nothing here polls, nothing reloads hits, nothing asks the server anything: a
 * search result is an answer to a question, not something to watch.
 *
 * Sources of the two facts that are easy to get wrong:
 *   core/css/apps.scss                              #app-content, overflow auto
 *   lib/public/AppFramework/Http/Response.php       the no-store default
 */
'use strict'

;(function () {
  // The one key in session storage this page owns. Session scoped on purpose:
  // the note is about the trip a visitor is on right now, and it is gone with
  // the tab.
  const STORAGE_KEY = 'findling:lasthit'

  // The class that marks the row, and the element inside it that says the same
  // thing to a screen reader. Colour alone marks nothing.
  const RETURNED_CLASS = 'findling-hit--returned'
  const RETURNED_TEXT = '.findling-hit__returned'

  const ROW_SELECTOR = '.findling-hit'
  const LINK_SELECTOR = '.findling-hit__link'
  const ROW_ID_PREFIX = 'findling-hit-'

  // The navigation the focus rule waits for. On a fresh visit no focus is
  // stolen; on a return the keyboard lands where the visitor left off.
  const NAVIGATION_BACK = 'back_forward'

  /**
   * Which list this is: the search term, the filter and the page number, all
   * three read out of the current address. A note taken on page three of one
   * search must not mark a row on page one of another, and the address is the
   * only place that knows which list is on screen.
   */
  function currentKey () {
    const params = new URLSearchParams(window.location.search)

    return JSON.stringify([
      params.get('query') || '',
      params.get('names') === '1',
      params.get('page') || '1'
    ])
  }

  /**
   * The file id in the id of a row, or null for anything that is not one.
   */
  function fileIdOf (row) {
    if (row === null || typeof row.id !== 'string' || !row.id.startsWith(ROW_ID_PREFIX)) {
      return null
    }

    const rest = row.id.slice(ROW_ID_PREFIX.length)
    if (!/^[0-9]+$/.test(rest)) {
      return null
    }

    return Number(rest)
  }

  /**
   * Writing the note under findling:lasthit. The key is named here and in the
   * reader below as well as in the constant, in the same spirit as the routes
   * of the administration script: a grep for the key has to find both the side
   * that writes it and the side that reads it, and a key that is only spelled
   * in one place is a key nobody finds when it moves.
   *
   * In a private window with storage locked the access throws,
   * and then the page loses this one marker and keeps everything else, rather
   * than putting an exception in the console of somebody who just clicked a
   * search result.
   */
  function remember (fileId) {
    try {
      window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ key: currentKey(), fileId: fileId }))
    } catch (error) {
      // Nothing to do and nothing to say. Stage three of the return contract is
      // off, stages one and two are untouched.
    }
  }

  /**
   * Reading findling:lasthit back, with the same protection and the same verdict for a value
   * that is not the shape this page wrote. The note is editable by whoever owns
   * the browser, so it is treated as input: it decides which row already in the
   * markup gets a class, and it never becomes an address, an element or a
   * request.
   */
  function recall () {
    let raw = null
    try {
      raw = window.sessionStorage.getItem(STORAGE_KEY)
    } catch (error) {
      return null
    }

    if (typeof raw !== 'string') {
      return null
    }

    let note = null
    try {
      note = JSON.parse(raw)
    } catch (error) {
      return null
    }

    if (note === null || typeof note !== 'object') {
      return null
    }
    if (typeof note.key !== 'string' || !Number.isInteger(note.fileId) || note.fileId < 0) {
      return null
    }

    return note
  }

  /**
   * Whether the row is on screen as it is. A position the browser restored by
   * itself is never overwritten, so the scroll below only happens when the row
   * would otherwise be out of sight.
   */
  function inSight (row) {
    const box = row.getBoundingClientRect()
    const height = window.innerHeight || document.documentElement.clientHeight

    return box.top >= 0 && box.bottom <= height
  }

  /**
   * Whether this visit is a return. The navigation type is reported whether or
   * not the page came from a cache, which is what makes it usable here.
   */
  function isReturn () {
    if (typeof window.performance === 'undefined' || typeof window.performance.getEntriesByType !== 'function') {
      return false
    }

    const entries = window.performance.getEntriesByType('navigation')

    return entries.length > 0 && entries[0].type === NAVIGATION_BACK
  }

  // Event one: the click. Delegated to the list so that there is one listener
  // for twenty five rows, and passive so that the browser knows this handler
  // will not hold the navigation up. The link is left alone entirely.
  const list = document.querySelector('.findling-hits')
  if (list !== null) {
    list.addEventListener('click', function (event) {
      const fileId = fileIdOf(event.target.closest(ROW_SELECTOR))
      if (fileId !== null) {
        remember(fileId)
      }
    }, { passive: true })
  }

  // Event two: the return. Three steps in this order, and each one is allowed to
  // be the last: a note for another list marks nothing, a row that is not on
  // this page is simply not found, and a fresh visit keeps its focus where the
  // template put it.
  window.addEventListener('pageshow', function () {
    const note = recall()
    if (note === null || note.key !== currentKey()) {
      return
    }

    const row = document.getElementById(ROW_ID_PREFIX + String(note.fileId))
    if (row === null) {
      return
    }

    // Step one: the marker itself, in both of its carriers.
    row.classList.add(RETURNED_CLASS)
    const spoken = row.querySelector(RETURNED_TEXT)
    if (spoken !== null) {
      spoken.removeAttribute('hidden')
    }

    // Step two: the position, and only when it is needed.
    if (!inSight(row)) {
      row.scrollIntoView({ block: 'center' })
    }

    // Step three: the keyboard, and only on the way back. preventScroll keeps
    // this from undoing the decision step two just made.
    if (isReturn()) {
      const link = row.querySelector(LINK_SELECTOR)
      if (link !== null) {
        link.focus({ preventScroll: true })
      }
    }
  })
})()
