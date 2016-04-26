/**
 * @ngdoc function
 * @name miller.directives:lazy
 * @description
 * # marked
 * transform markdown data in miller enhanced datas
 */
angular.module('miller')
  .directive('mde', function ($log, $timeout, $modal, DocumentFactory, RUNTIME) {
    return {
      restrict: 'AE',
      scope: {
        mde: '=',
        settoc: '&',
        setdocs: '&'
      },
      templateUrl: RUNTIME.static + 'templates/partials/mde.html',
      link: function(scope, el, attributes){
        console.log('MDE',el)
        var simplemde,
            timer,
            timer_recompile,
            wand = el.find('.wand').hide(),
            textarea = el.find('textarea').hide(),
            lookups=[],
            renderer = new marked.Renderer(),
            referenceModal = $modal({
              scope: scope,
              title: 'h',
              template: RUNTIME.static + 'templates/partials/modals/mde-enrich.html',
              show: false
            });

        function init(){
          textarea.show();
          wand.show();

          simplemde = new SimpleMDE({
            element: textarea[0],
            spellChecker: false,
            status: false,
            toolbar: false,
            initialValue: scope.mde
          });
          
          var cursor,
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
                  left: simplemde.codemirror.display.cursorDiv.firstChild.offsetLeft
                };
                wand.css('transform', 'translateY('+cursor.top+'px)');
              }
            }, 10);
            
          }

          /*
            @todo: Should be put as angular filter.
          */
          function slugify(text){
            var strip  = /[^\w\s-]/g,
                hyphen = /[-\s]+/g,
                slug   = text.toLowerCase();

            var map = {
              from: 'àáäãâèéëêìíïîòóöôõùúüûñç·/_,:;', 
              to  : 'aaaaaeeeeiiiiooooouuuunc------'
            };

            
            for (var i=0, j=map.from.length; i<j; i++) {
              slug = slug.replace(new RegExp(map.from.charAt(i), 'g'), map.to.charAt(i));
            }
            return slug.replace(strip, '').trim().replace(hyphen, '-');
          }

          /*
            Recompile with marked, analyzing the documents and
            the different stuff in the contents
          */
          function recompile(){
            // $log.debug('::mde -> recompile() ...');
            var _ToC = [],
                _ToCHash;
            renderer.heading = function(text, level){
              // toc is empty
              var h = {
                text: text,
                level: level,
                slug: slugify(text)
              };
              _ToC.push(h);
            };

            marked(simplemde.value(), {
              renderer: renderer
            });

            _ToCHash = md5(JSON.stringify(_ToC))
            if(_ToCHash != ToCHash){
              ToCHash = _ToCHash;
              $log.log('::mde -> recompile() items:',_ToC, ' (differences)');
              scope.settoc({items:_ToC});
              scope.$apply();
            }
          }


          simplemde.codemirror.on('update', function(e){
            $log.debug('::mde @codemirror.update');
            var value = simplemde.value();
            if(textarea.val() != value){
              scope.mde = value; // set model
              textarea.val(value); // get headers after some time
              scope.$apply();
            }
            move();

            if(timer_recompile)
              clearTimeout(timer_recompile);
            timer_recompile = setTimeout(recompile, 500);
            
          });

          simplemde.codemirror.on('cursorActivity', move);
          
          timer_recompile = setTimeout(recompile, 0);
          
          
          
        };


        /*
          Modal tabs
        */
        // open
        scope.showReferenceModal = function(){
          $log.debug('::mde -> showReferenceModal')
          referenceModal.$promise.then(function(){
            $log.debug('::mde -> showReferenceModal done')
            
            referenceModal.show();
          });
          
          DocumentFactory.get(function(res){
            console.log('list', res)
            $log.debug('::mde -> showReferenceModal loaded', res.results)
            
            scope.lookups = res.results;
          })
          // console.log(simplemde)
          // debugger
        }

        scope.addDocument = function(){
          if(!scope.selectedDocument) {
            $log.warning('::mde -> addDocument() no document selected')
          } 
          $log.debug('::mde -> addDocument() doc:', scope.selectedDocument);
          // lock ui
          // draw link at the end of the db

          referenceModal.hide();
          SimpleMDE.drawLink(simplemde,{
            url: scope.selectedDocument.slug
          });
        }

        scope.selectDocument = function(doc){
          if(scope.selectedDocument)
            scope.selectedDocument.isSelected = false;
          if(scope.selectedDocument && scope.selectedDocument.id == doc.id){
            scope.isSomethingSelected = false;
            scope.selectedDocument = false;
          } else {
            doc.isSelected = true;
            scope.isSomethingSelected = true;
            scope.selectedDocument = doc;
          }
          
          
        }
        
        // take into account custom font-face rendering.
        $timeout(init, 200);
        return;


      }
    };
  })