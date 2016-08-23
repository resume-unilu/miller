/**
 * @ngdoc function
 * @name miller.directives:lazy
 * @description
 * # marked
 * transform markdown data in miller enhanced datas
 */
angular.module('miller')
  .directive('mde', function ($log, $timeout, $modal,  $filter, DocumentFactory, StoryFactory, OembedSearchFactory, embedService, markedService, RUNTIME) {
    return {
      restrict: 'AE',
      scope: {
        mde: '=',
        settoc: '&',
        setdocs: '&'
      },
      templateUrl: RUNTIME.static + 'templates/partials/mde.html',
      link: function(scope, el, attributes){
        // active tab
        scope.activeStates = [];

        // preview enabled or disabled
        scope.isPreviewEnabled = false;

        // secretize bookmarks. Automatically clean the code sent to initialvalue
        // will set SetBookmarks 


        var simplemde,
            timer,
            timer_recompile,
            timer_preview,
            wand = el.find('.wand').hide(),
            textarea = el.find('textarea').hide(),
            toolbox =  el.find('.toolbox').hide(),
            lookups=[],
            referenceModal = $modal({
              scope: scope,
              title: 'h',
              template: RUNTIME.static + 'templates/partials/modals/mde-enrich.html',
              show: false
            });
            
        function init(){
          textarea.show();
          wand.show();
          toolbox.show();

          simplemde = new SimpleMDE({
            element: textarea[0],
            spellChecker: false,
            status: false,
            toolbar: false,
            toolbarTips: false,
            initialValue: scope.mde
          });

          // assign overlay
          // simplemde.codemirror.addOverlay({
          //     name: 'invisibles',
          //     token:  function nextToken(stream) {
          //         var ret,
          //             spaces  = 0,
          //             peek    = stream.peek() === ' ';

          //         if (peek) {
          //             while (peek && spaces < Maximum) {
          //                 ++spaces;

          //                 stream.next();
          //                 peek = stream.peek() === ' ';
          //             }

          //             ret = 'whitespace whitespace-' + spaces;
          //         } else {
          //             while (!stream.eol() && !peek) {
          //                 stream.next();

          //                 peek = stream.peek() === ' ';
          //             }

          //             ret = 'cm-eol';
          //         }

          //         return ret;
          //     }
          // });

          
          var cursor,
              pos,
              stat,
              followCursor,
              // table of contents hash. Are there differences?
              pcursor;// = simplemde.codemirror.display.find('.Codemirror-cursor');


          // listener codemirror@cursorActivity
          function move(){
            if(timer)
              clearTimeout(timer);

            timer = setTimeout(function(){

              if(simplemde.codemirror.display.cursorDiv.firstChild){
                // console.log('moving cruising', simplemde.codemirror.getSelection(), 'crui')
                
                cursor = {
                  top: simplemde.codemirror.display.cursorDiv.firstChild.offsetTop,
                  left: simplemde.codemirror.display.cursorDiv.firstChild.offsetLeft,
                  height: simplemde.codemirror.display.cursorDiv.firstChild.offsetHeight
                };
                wand.css('transform', 'translateY('+(cursor.top+cursor.height-20)+'px)');
                
                if(followCursor)
                  toolbox.css('transform', 'translate('+(cursor.left)+'px,'+(cursor.top)+'px)');

                // check cursor position: is it inside a BOLD or ITALIC?
                pos = simplemde.codemirror.getCursor("start");
                stat = simplemde.codemirror.getTokenAt(pos);
                // $log.log('     ', stat)
                scope.activeStates = (stat.type || '').split(' ');
                scope.$apply();
              }
            }, 20);
            

          }

          // // listener for the selection object.
          var _isSelection;
          function beforeSelectionChange(e, sel){
            var isSelection = (sel.ranges[0].head.ch - sel.ranges[0].anchor.ch) !== 0;
            // selection is on and it has changed. 
            if(isSelection && isSelection != _isSelection){
              toolbox.addClass('active');
            } else if(!isSelection && isSelection != _isSelection){
              toolbox.removeClass('active');
            }
            
            _isSelection = isSelection
          }

          

          /*
            Recompile with marked, analyzing the documents and
            the different stuff in the contents.
          */
          var _ToCHash,
              _docsHash;

          function recompile(){
            // $log.debug('::mde -> recompile() ...');
            var marked   = markedService(simplemde.value()),
                ToCHash = md5(JSON.stringify(marked.ToC)),
                docsHash = md5(_.map(marked.docs,'slug').join('--'));
            
            if(_ToCHash != ToCHash){
              $log.log('::mde -> recompile() items ToC:',marked.ToC.length, 'docs:', marked.docs.length, ToCHash);
              scope.settoc({items:marked.ToC});
            }
            if(_docsHash != docsHash){
              $log.log('::mde -> recompile() items docs:', _docsHash);
              scope.setdocs({documents: marked.docs});
            }
            // scope.$apply();
            // apply toc hash not to reload twice
            _ToCHash = ToCHash;
            _docsHash = docsHash;
          }

          // listener codemirror@update
          // update event, recompile after n milliseconds
          function onUpdate(e){
            var value = simplemde.value();
            if(textarea.val() != value){
              scope.mde = value; // set model
              textarea.val(value); // get headers after some time
            }
            move();
            if(timer_recompile)
              clearTimeout(timer_recompile);
            timer_recompile = setTimeout(function(){
              recompile();
              scope.$apply()
            }, 500);  
          }

          // listener codemirror@changeEnd
          function onChange(e, change){
            var from = change.from;
            var text = change.text.join("\n");
            var removed = change.removed.join("\n");
            var to =  simplemde.codemirror.posFromIndex(simplemde.codemirror.indexFromPos(from) + text.length);

            simplemde.codemirror.markText(from, to, {
              className: 'mde-modified'
            })
          };

          // listener codemirror@focus
          function onFocus(e) {
            toolbox.show();
            wand.show()
          };
          // listener codemirror@focus
          function onBlur(e) {
            toolbox.hide();
            wand.hide();
          };
          // listener
          function beforeChange(){
            // debugger
          }

          simplemde.codemirror.on('update', onUpdate);
          simplemde.codemirror.on('cursorActivity', move);
          simplemde.codemirror.on('beforeSelectionChange', beforeSelectionChange);
          simplemde.codemirror.on('beforeChange', beforeChange);
          simplemde.codemirror.on('change', onChange);
          // simplemde.codemirror.on('focus', onFocus);
          // simplemde.codemirror.on('blur', onBlur);
          
          // if a settoc, ask for recompiling
          if(scope.settoc)
            timer_recompile = setTimeout(recompile, 20);
        
        }

        // listen window event, instance specific
        var _isToolbarVisible;
        $(window).on('scroll.mde', function(){
          var toolbarOffset = el.offset().top - st,
              isToolbarVisible =  toolbarOffset > 100;

          if(!isToolbarVisible)
            toolbox.css('transform', 'translate(0px,'+(100 - toolbarOffset)+'px)');
          else if(isToolbarVisible!==_isToolbarVisible)
            toolbox.css('transform', 'translate(0px,0px)');
          

          _isToolbarVisible = isToolbarVisible;
        });

        // on destry, destroy scroll event
        scope.$on("$destroy", function(){
          $(window).off('scroll.mde');
        });

        /*
          Modal tabs
        */

        // open modal tab and store previously open tab in this scope.
        scope.setTab = function(tab){
          scope.tab = tab;
        };
        scope.tab = 'CVCE';

        // preview url
        scope.previewUrl = function(url){
          if(timer_preview)
            $timeout.cancel(timer_preview);
          // check url
          var regexp = /(ftp|http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&&#37;@!\-\/]))?/;
          if(!regexp.test(url)){
            $log.error('::mde -> previewUrl() url provided:', url, 'is not valid');
            return false;
          }
          url = url.replace('#', '.hash.');
          timer_preview = $timeout(function(){
            $log.debug('::mde -> previewUrl() url:', url);
            scope.suggestMessage = '(loading...)';
            embedService.get(url).then(function(data){
              $log.debug(':: mde -> previewUrl() received:', data)
              scope.embed = data;
              scope.suggestMessage = '(<b>done</b>)';
            });
          }, 20);
        };

        // suggest from different archives, w timeout
        scope.suggestResults = [];
        scope.suggestMessage = '';
        scope.suggest = function(query, service){
          $log.log('::mde -> suggest()', scope.query, query, OembedSearchFactory);
          scope.suggestMessage = '(loading...)';
          // internal search
          if(service == 'favourite'){
            DocumentFactory.get({
              filters: JSON.stringify(query.length > 2? {contents__icontains: query}: {})
            },function(res){
              $log.log('::mde -> showReferenceModal documents loaded', res.results.length);

              scope.lookups = res.results;
              scope.suggestMessage = '(<b>' + res.count + '</b> results)';
            });
            return;
          }

          if(service == 'glossary') {
            var params = {
              tags__slug: 'glossary'
            }
            if(query.length > 2)
              params.contents__icontains = query;

            StoryFactory.get({
              filters: JSON.stringify(params)
            },function(res){
              $log.log('::mde -> showReferenceModal documents loaded', res.results.length);

              scope.glossary = res.results;
              scope.suggestMessage = '(<b>' + res.count + '</b> results)';
            });
            return;
          } 

          if(query.length < 3) {
            scope.suggestMessage = '(write something more)';
            scope.suggestResults = [];
            return;
          }

            // external search
          
          if(OembedSearchFactory[service])
            OembedSearchFactory[service](query).then(function(res){
              scope.suggestResults = res.data.results;
              scope.suggestMessage = '(<b>' + res.data.count + '</b> results)';
            });
          
        };

        // open
        scope.showReferenceModal = function(){
          if(scope.activeStates.indexOf("link") !== -1){
            $log.warn('oh dear, you should not click on it')
            return;
          }
          // if there is already a link, should add it.
          referenceModal.$promise.then(function(){
            $log.log('::mde -> showReferenceModal called');
            referenceModal.show();
          });
          
          DocumentFactory.get(function(res){
            $log.log('::mde -> showReferenceModal documents loaded', res.results.length);

            scope.lookups = res.results;
          });
          // console.log(simplemde)
          // debugger
        };

      

        scope.addDocument = function(type, contents, reference, url, embed){
          var slug;

          $log.debug('::mde -> addDocument() type:', type);

          if(type=='bibtex'){
            $log.debug('    reference:', bibtexParse.toJSON(reference));
            return;
          }

          if(type=='glossary'){
            referenceModal.hide();
            SimpleMDE.drawLink(simplemde,{
              // text: scope.selectedDocument.title,
              url: 'voc/' + scope.selectedDocument.slug
            });
            return;
          }
          // case it is an url
          if(type=='url'){
            if(!embed.title){
              referenceModal.hide();
              SimpleMDE.drawLink(simplemde,{
                url: url
              });
              return;
            }
            slug = $filter('slugify')(embed.title).substr(0,100);

            DocumentFactory.save({
              title: embed.title,
              contents: JSON.stringify(embed),
              type: (embed.type|| 'link').toLowerCase(),
              slug:  slug,
              url: url
            }, function(res){
              $log.debug('::mde -> addDocument() document saved:', res.slug, res.id, res.short_url);
              if(res.slug){
                referenceModal.hide();
                SimpleMDE.drawLink(simplemde,{
                  url: 'doc/' + res.slug
                });
              }
            }, function(err){
              // ignore duplicates (slug field) and put it directly.
              if(err.data.slug && _.keys(err.data).join('') == 'slug'){
                SimpleMDE.drawLink(simplemde,{
                  url: 'doc/' + slug
                });
              } else {
                $log.error('::mde -> addDocument() cannot save document', err);
              }
            });
            return;
          }

          if(!scope.selectedDocument) {
            $log.warn('::mde -> addDocument() no document selected');
            return;
          }

          if(type == 'CVCE'){
            slug = 'cvce/'+scope.selectedDocument.details.doi;
            $log.debug('::mde -> addDocument() doc:', slug);
            DocumentFactory.save({
              title: scope.selectedDocument.title,
              contents: JSON.stringify(scope.selectedDocument),
              type: (scope.selectedDocument.type|| 'link').toLowerCase(),
              slug:  slug,
              url: url
            }, function(res){
              $log.debug('::mde -> addDocument() document saved:', res.slug, res.id, res.short_url);
              if(res.slug){
                referenceModal.hide();
                SimpleMDE.drawLink(simplemde,{
                  url: 'doc/' + res.slug
                });
              }
            }, function(err){
              // debugger
              // ignore duplicates and put it directly.
              if(err.data.slug){
                $log.debug('::mde -> addDocument() document already saved:', slug);
                SimpleMDE.drawLink(simplemde,{
                  url: 'doc/' + slug
                });
              }
            });
            return;
          }

          // document type
          if(scope.selectedDocument.type == 'bibtex'){
            
            SimpleMDE.drawLink(simplemde,{
              // text: '('+ scope.selectedDocument.metadata.author + ' '+ scope.selectedDocument.metadata.year +')',
              url: 'doc/' + scope.selectedDocument.slug
            });
          }
          // the document has been selected.
          $log.debug('::mde -> addDocument() doc:', scope.selectedDocument);
          // lock ui
          // draw link at the end of the db
          referenceModal.hide();
          SimpleMDE.drawLink(simplemde,{
            url: 'doc/' + scope.selectedDocument.slug
          });
        };

        scope.selectDocument = function(doc){
          $log.log('::mde -> selectDocument()', doc.url);

          if(scope.selectedDocument && scope.selectedDocument.url == doc.url){
            // $log.log('::mde -> selectDocument() unselecting previous', doc.url);
            scope.isSomethingSelected = false;
            scope.selectedDocument = false;
          } else if(scope.selectedDocument){
            // $log.log('::mde -> selectDocument() change selection from', scope.selectedDocument.title);
            scope.isSomethingSelected = true;
            scope.selectedDocument = doc;
          } else {
            // $log.log('::mde -> selectDocument() as new item');
            scope.isSomethingSelected = true;
            scope.selectedDocument = doc;
          }
          
          
        };

        scope.action = function(action) {
          if(action == 'togglePreview'){
            scope.isPreviewEnabled = !scope.isPreviewEnabled;
          }
          SimpleMDE[action](simplemde);
        };
        
        // take into account custom font-face rendering.
        $timeout(init, 500);
        return;


      }
    };
  });