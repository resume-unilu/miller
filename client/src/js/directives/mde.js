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
      },
      templateUrl: RUNTIME.static + 'templates/partials/mde.html',
      link: function(scope, el, attributes){
        console.log('MDE',el)
        var simplemde,
            timer,
            wand = el.find('.wand').hide(),
            textarea = el.find('textarea').hide(),
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

          simplemde = new SimpleMDE({
            element: textarea[0],
            spellChecker: false,
            status: false,
            toolbar: false,
            initialValue: scope.mde
          });
          
          var cursor,
              pcursor;// = simplemde.codemirror.display.find('.Codemirror-cursor');

          function move(){
            if(timer)
              clearTimeout(timer);

            timer = setTimeout(function(){
              if(simplemde.codemirror.display.cursorDiv.firstChild){
                console.log('moving cruising')
                cursor = {
                  top: simplemde.codemirror.display.cursorDiv.firstChild.offsetTop,
                  left: simplemde.codemirror.display.cursorDiv.firstChild.offsetLeft
                };
                wand.css('transform', 'translateY('+cursor.top+'px)');
              }
            }, 10);
            
          }

          simplemde.codemirror.on('update', function(e){
            var value = simplemde.value();
            if(textarea.val() != value){
              scope.mde = value; // set model
              textarea.val(value); // get headers after some time
              scope.$apply();
            }
            move();

            
          });
          console.log('simplemde:', simplemde)
          simplemde.codemirror.on('cursorActivity', move);
          
          
          
          
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
          $log.debug('::mde -> addDocument() doc:', scope.selectedDocument)       
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