var o_hash = {
    /**
     *
     *  changing, reading, and initiating a session from the browser hash
     *
     **/

    // updates the hash according to user selections
    updateHash: function(){

      hash = [];
      for (var param in opus.selections) {
          if (opus.selections[param].length){
              hash[hash.length] = param + '=' + opus.selections[param].join(',').replace(/ /g,'+');
          }
      }

      o_widgets.pauseWidgetControlVisibility(opus.selections);

      for (var key in opus.extras) {

          try {
              hash[hash.length] = key + '=' + opus.extras[key].join(',');
          } catch(e) {
              // oops not an arr
              hash[hash.length] = key + '=' + opus.extras[key];
          }
      }
      for (key in opus.prefs) {

          if (key in ['widgets','widgets2','cols']) {

              hash[hash.length] = key + '=' + opus.prefs.widgets.join(',').replace(/\s+/g, '');

          } else if (key == 'page') {

            // page is stored like {"gallery":1, "data":1, "colls_gallery":1, "colls_data":1 }
            // so the curent page depends on the view being shown
            // opus.prefs.view = search, browse, collection, or detail
            // opus.prefs.browse =  'gallery' or 'data',
            page = o_browse.getCurrentPage();

            hash[hash.length] = 'page=' + page;


          } else if (key == 'widget_size' || key == 'widget_scroll') {
              // these are prefs having to do with widget resize and scrolled
              if (key == 'widget_scroll') { continue; } // there's no scroll without size, so we handle scroll when size comes thru

              for (slug in opus.prefs[key]) {
                  hash[hash.length] = o_widgets.constructWidgetSizeHash(slug);
              }

          } else {

            hash[hash.length] = key + '=' + opus.prefs[key];
          }
      }
      window.location.hash = '/' + hash.join('&');
    },

    // returns the hash part of the url minus the #/ symbol
    getHash: function(){
        if (window.location.hash) {
            return window.location.hash.match(/^#\/(.*)$/)[1];
        } else {
            return '';
        }
    },

    // part is part of the hash, selections or prefs
    getSelectionsFromHash: function() {
        var hash = o_hash.getHash();
        var pairs;
        if (!hash) return;

        if (hash.search('&') > -1) {
            pairs = hash.split('&');
        }
        else pairs = [hash];
        var selections = {};  // the new set of pairs that will not include the result_table specific session vars

        for (var i=0;i< pairs.length;i++) {
            var param = pairs[i].split('=')[0];
            var value = pairs[i].split('=')[1];
            if (!param) continue;
            if (!(param in opus.prefs) && !param.match(/sz-.*/)) {

            if (param in selections) {
                selections[param].push(value);
            } else {
                selections[param] = [value];
                }
            } else {
                if (param  == 'qtype-phase') {}
            }
        }
        if (!jQuery.isEmptyObject(selections)) {
            return selections;
        }

    },


    initFromHash: function(){
        hash = o_hash.getHash();
        if (!hash) { return; }
        // first are any custom widget sizes in the hash?
        // just updating prefs here..
        hash = hash.split('&');

        for (var q in hash) {

            slug = hash[q].split('=')[0];
            value = hash[q].split('=')[1];

            if (slug.match(/sz-.*/)) {
                var id = slug.match(/sz-(.*)/)[1];
                // opus.extras['sz-' + id] = value;
                opus.prefs.widget_size[id] = value.split('+')[0];

                if (value.split('+')[1])
                    opus.prefs.widget_scroll[id] = value.split('+')[1];
            }
            else if (slug.match(/qtype-.*/)) {
                // range drop down, add the qtype to the global extras array
                var id = slug.match(/qtype-(.*)/)[1];
                opus.extras['qtype-' + id] = value.split(',');
            }
            // look for prefs
            else if (slug in opus.prefs) {

                if (slug == 'widgets' || slug == 'widgets2') {
                    if (value) {
                        opus.prefs[slug] = value.replace(/\s+/g, '').split(',');
                    }
                } else if (slug == 'page') {
                    if (value) {
                        opus.prefs.page['gallery'] = parseInt(value, 10);
                        opus.prefs.page['data'] = parseInt(value, 10);
                    }
                } else if (slug == 'limit') {
                    if (value) {
                        opus.prefs[slug] = parseInt(value, 10);
                    }
                } else if (slug=='cols') {
                    if (value) {
                        opus.prefs[slug] = value.split(',');
                    }
                }
                else if (value) {
                        opus.prefs[slug] = value;
                }

            } else {
                // these are search params/value!
                if (value) {
                    opus.selections[slug]= value.split(',');
                }
            }
        }

        // despite what the url says, make sure every widget that is constrained is actually visible
        for (slug in opus.selections) {
          if (jQuery.inArray(opus.prefs['widgets']) < 0) {
            opus.prefs['widgets'].push(slug);
          }
        }

        if (!jQuery.isEmptyObject(opus.last_selections)) {
            opus.load();
        }
    },


};
