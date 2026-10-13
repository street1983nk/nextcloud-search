/**
 * The filter entries of Findling in the menu of the unified search.
 *
 * Seven entries: one per type group, in the order of SearchFilters::TYPES, and
 * one that narrows the hits to a folder. Each entry becomes a chip of the
 * Findling result group, and the value the entry stands for travels with that
 * chip as a query parameter of the provider request (types or folder), which
 * Search\Provider declares as custom filters and reads in silence.
 *
 * Why this file exists at all. A custom filter a provider declares has no
 * surface in the unified search of Nextcloud 33 to 35; the modal renders its own
 * filters and nothing else. The one way an app gets a visible entry into that
 * menu is OCA.UnifiedSearch.registerFilterAction, the API the Files app uses for
 * its "In folder" entry. LoadUnifiedSearchFiltersListener loads this file on
 * every page of a logged in user, because the search opens from every header.
 *
 * Why plain JavaScript. No module, no bundler, no dependency and no package
 * file anywhere in this app, the same as search.js and admin.js. The script
 * builds no markup and asks the server nothing: it hands four plain values to
 * the core (an id, a label, an icon address and a callback) and, on a click,
 * one event with a text and a parameter. The core renders all of it as text.
 *
 * Why the event goes out in a setTimeout. The core calls the callback of an
 * entry BEFORE it pushes the chip into its list, and the event handler only
 * attaches parameters to a chip that is already there. An event sent inside the
 * callback finds no chip and is lost; one turn of the event loop later the chip
 * exists.
 *
 * Why every click sends, also on an entry that is already applied. A second
 * click on an applied entry makes the core remove the chip and push a fresh one
 * without parameters. Sending again is what keeps the fresh chip filtered; the
 * folder entry sends the folder it remembers instead of asking again.
 *
 * Why the root sends no folder. A parameter with an empty value is refused by
 * the core with HTTP 400 before Findling is asked, and the root of the user
 * folder means no narrowing at all. So the root, or a choice that is no path,
 * sends an empty parameter object and never an empty string.
 *
 * Feature detection before every API. The legacy search has no
 * OCA.UnifiedSearch, the folder picker of OC.dialogs is deprecated, and a page
 * of another app must never break because of this file. Where an API is
 * missing, the entry that needs it is not registered and nothing is thrown.
 *
 * Sources of the three core facts, nextcloud/server stable33 to stable35:
 *   core/src/unified-search.ts                          registerFilterAction
 *   core/src/components/UnifiedSearch/UnifiedSearchModal.vue
 *     addProviderFilter    stable34:674-704, stable35:1212-1240 (callback first, chip second)
 *     handlePluginFilter   stable34:828-845, stable35:1365-1380 (parameters on an existing chip)
 *   apps/files/src/plugins/search/folderSearch.ts       the same mechanism for "In folder"
 */
'use strict'

;(function () {
  // The app id and the provider id of Findling. Entries carry it as appId (the
  // group of the menu) and as searchFrom (the provider the chip asks), never as
  // their own id: the core matches chips and providers by id, and an entry
  // called findling would collide with the provider itself.
  const APP_ID = 'findling'

  const TYPE_ID_PREFIX = 'findling-type-'
  const FOLDER_ID = 'findling-folder'

  const ADD_FILTER_EVENT = 'nextcloud:unified-search:add-filter'
  const FOLDER_MIMETYPE = 'httpd/unix-directory'

  // The six groups as [group, English key], in the order of SearchFilters::TYPES.
  // The group is the wire value of the types filter; the key is the group name
  // every catalogue of this app already carries.
  const TYPE_ENTRIES = [
    ['pdf', 'PDF'],
    ['documents', 'Documents'],
    ['spreadsheets', 'Spreadsheets'],
    ['presentations', 'Presentations'],
    ['images', 'Images'],
    ['text', 'Text'],
  ]

  // The translation function of the core, or the source string where it is
  // missing, so a label is never undefined.
  const t = typeof window.t === 'function'
    ? window.t
    : function (app, text) { return text }

  // The folder chosen last, as a path relative to the user folder ('/' for the
  // root), or null before the first choice. Only ever sent back to the core.
  let chosenFolder = null

  /** A function that never lets an error out into the page of somebody else. */
  function guarded (fn) {
    return function () {
      try {
        return fn.apply(this, arguments)
      } catch (error) {
        return undefined
      }
    }
  }

  /**
   * The template with %s replaced by a value, taken literally: a replacement
   * string would read $& or $' inside a folder name as a pattern.
   */
  function filled (template, value) {
    return template.replace('%s', function () { return value })
  }

  function appIcon () {
    const oc = window.OC
    return oc && typeof oc.imagePath === 'function' ? oc.imagePath(APP_ID, 'app') : ''
  }

  /** Send the event one turn later, after the core has pushed the chip. */
  function sendLater (detail) {
    setTimeout(guarded(function () {
      const bus = window._nc_event_bus
      if (bus && typeof bus.emit === 'function') {
        bus.emit(ADD_FILTER_EVENT, detail)
      }
    }), 0)
  }

  function folderPicker () {
    const dialogs = window.OC && window.OC.dialogs
    return dialogs && typeof dialogs.filepicker === 'function' ? dialogs : null
  }

  /**
   * The picked path as '/a/b', with one leading and no trailing slash, '/' for
   * the root, or null for anything that is not a string.
   */
  function normalizedFolder (picked) {
    if (typeof picked !== 'string') {
      return null
    }
    return '/' + picked.replace(/^\/+|\/+$/g, '')
  }

  function sendFolder (folder) {
    const parts = folder.split('/')
    const name = parts[parts.length - 1] !== '' ? parts[parts.length - 1] : '/'
    const params = {}
    if (folder !== '' && folder !== '/') {
      params.folder = folder
    }
    sendLater({
      id: FOLDER_ID,
      appId: APP_ID,
      searchFrom: APP_ID,
      filterUpdateText: filled(t('findling', 'File contents in %s'), name),
      filterParams: params,
    })
  }

  /**
   * Open the folder picker of the core. A cancelled picker sends nothing, the
   * same as the "In folder" entry of the Files app: the chip stays and searches
   * without a folder until a folder is chosen.
   */
  function pickFolder () {
    const dialogs = folderPicker()
    if (dialogs === null) {
      return
    }
    dialogs.filepicker(
      t('findling', 'Choose the folder to search in'),
      guarded(function (picked) {
        const folder = normalizedFolder(picked)
        if (folder === null) {
          return
        }
        chosenFolder = folder
        sendFolder(folder)
      }),
      false,
      [FOLDER_MIMETYPE],
      true,
      dialogs.FILEPICKER_TYPE_CHOOSE,
      '/',
      { allowDirectoryChooser: true },
    )
  }

  function registerTypeEntry (api, entry) {
    const group = entry[0]
    const id = TYPE_ID_PREFIX + group
    const label = filled(t('findling', 'File contents: %s'), t('findling', entry[1]))
    api.registerFilterAction({
      id: id,
      appId: APP_ID,
      searchFrom: APP_ID,
      label: label,
      icon: appIcon(),
      callback: guarded(function () {
        sendLater({
          id: id,
          appId: APP_ID,
          searchFrom: APP_ID,
          filterUpdateText: label,
          filterParams: { types: group },
        })
      }),
    })
  }

  function registerFolderEntry (api) {
    api.registerFilterAction({
      id: FOLDER_ID,
      appId: APP_ID,
      searchFrom: APP_ID,
      label: t('findling', 'File contents in a folder'),
      icon: appIcon(),
      // apply is false when the entry is already applied: the core is about to
      // replace the chip with one without parameters, so the remembered folder
      // goes out again. Before any choice the picker opens instead.
      callback: guarded(function (apply) {
        if (apply === false && chosenFolder !== null) {
          sendFolder(chosenFolder)
          return
        }
        pickFolder()
      }),
    })
  }

  const start = guarded(function () {
    const oca = window.OCA
    const api = oca && oca.UnifiedSearch
    if (!api || typeof api.registerFilterAction !== 'function') {
      return
    }
    TYPE_ENTRIES.forEach(function (entry) {
      registerTypeEntry(api, entry)
    })
    if (folderPicker() !== null) {
      registerFolderEntry(api)
    }
  })

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start)
  } else {
    start()
  }
})()
