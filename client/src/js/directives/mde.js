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


          
          var cursor,
              pos,
              stat,
              followCursor,
              // table of contents hash. Are there differences?
              ToCHash = '',
              pcursor;// = simplemde.codemirror.display.find('.Codemirror-cursor');

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
                // $log.log('     ', stat, pos, simplemde.codemirror)
                scope.activeStates = (stat.type || '').split(' ');
                scope.$apply();
              }
            }, 20);
            

          }

          // // listener for the selection object.
          // function beforeSelectionChange(e, sel){
          //   var isSelection = (sel.ranges[0].head.ch - sel.ranges[0].anchor.ch) !== 0;
            
          //   if(!isSelection && followCursor !== isSelection){
          //     toolbox.css('transform', 'translate(0px,0px)');
          //   }
          //   followCursor = isSelection;
          // }

          

          /*
            Recompile with marked, analyzing the documents and
            the different stuff in the contents.
          */
          function recompile(){
            // $log.debug('::mde -> recompile() ...');
            var marked   = markedService(simplemde.value()),
                _ToCHash = md5(JSON.stringify(marked.ToC));

            $log.log('::mde -> recompile() items ToC:',marked.ToC.length, 'docs:', marked.docs.length);

            // if(_ToCHash != ToCHash){
            //   ToCHash = _ToCHash;
              scope.settoc({items:marked.ToC});
              scope.setdocs({documents: marked.docs});
              scope.$apply();
            // }
            // save the new documents?
            
          }

          // listener codemirror@update
          simplemde.codemirror.on('update', function(e){
            var value = simplemde.value();
            if(textarea.val() != value){
              scope.mde = value; // set model
              textarea.val(value); // get headers after some time
            }
            move();
            if(timer_recompile)
              clearTimeout(timer_recompile);
            timer_recompile = setTimeout(recompile, 500);  
          });

          // listener codemirror@cursorActivity
          simplemde.codemirror.on('cursorActivity', move);
          
          // if a settoc, ask for recompiling
          if(scope.settoc)
            timer_recompile = setTimeout(recompile, 0);
        
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
          console.log('dkflskflskfsmlkfsdf', toolbarOffset )
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
            $log.error('::mde -> previewUrl url provided:', url, 'is not valid');
            return false;
          }
          url = url.replace('#', '.hash.');
          timer_preview = $timeout(function(){
            $log.debug('::mde -> previewUrl', url);
            embedService.get(url).then(function(data){
              scope.embed = data;
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
            debugger
            SimpleMDE.drawLink(simplemde,{
              url: 'voc/' + scope.selectedDocument.slug
            });
            return;
          }
          // case it is an url
          if(type=='url'){
            slug = $filter('slugify')(embed.title);

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
              // debugger
              // ignore duplicates and put it directly.
              if(err.data.slug){
                SimpleMDE.drawLink(simplemde,{
                  url: 'doc/' + slug
                });
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
          $log.log('::mde -> selectDocument()', doc);
          if(scope.selectedDocument)
            scope.selectedDocument.isSelected = false;
          if(scope.selectedDocument && (scope.selectedDocument.id == doc.id)){
            scope.isSomethingSelected = false;
            scope.selectedDocument = false;
          } else {
            doc.isSelected = true;
            scope.isSomethingSelected = true;
            scope.selectedDocument = doc;
          }
          
          
        };

        scope.action = function(action) {
          SimpleMDE[action](simplemde);
        };
        
        // take into account custom font-face rendering.
        $timeout(init, 200);
        return;


      }
    };
  });