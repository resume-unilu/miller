/**
 * @ngdoc function
 * @name miller.directives:lazy
 * @description
 * # marked
 * transform markdown data in miller enhanced datas
 */
angular.module('miller')
  .directive('mde', function ($log, $timeout) {
    return {
      restrict: 'AE',
      scope: {
        mde: '=',
      },

      link: function(scope, el, attributes){

        el.hide();
        var wand = $('#wand');

        function init(){
          el.show();
          var simplemde = new SimpleMDE({
            element: el[0],
            spellChecker: false,
            status: false,
            toolbar: false,
            initialValue: scope.mde
          });
          
          var cursor,
              pcursor;// = simplemde.codemirror.display.find('.Codemirror-cursor');

          simplemde.codemirror.on('update', function(e){
            var value = simplemde.value();
            if(el.val() != value){
              scope.mde = value; // set model
              el.val(value);
              scope.$apply();
            }
            move();

            
          });

          function move(){
            cursor = {
              top: simplemde.codemirror.display.cursorDiv.firstChild.offsetTop,
              left: simplemde.codemirror.display.cursorDiv.firstChild.offsetLeft
            };
            wand.css('transform', 'translateY('+cursor.top+'px)')
          }

          simplemde.codemirror.on('cursorActivity', move);

          // simplemde.codemirror.on('cursorActivity', function(e){
          //   cursor = {
          //     top: simplemde.codemirror.display.cursorDiv.firstChild.offsetTop,
          //     left: simplemde.codemirror.display.cursorDiv.firstChild.offsetLeft
          //   };

          //   wand.css('transform', 'translateY('+cursor.top+'px)')
            
          //   pcursor = cursor
          //   // console.log($(simplemde.codemirror.display.cursorDiv).css('top'))
          //   console.log(cursor)
          //   // debugger
          // })
        }

        $timeout(init, 200)
        

       
        return;

        // simplemde.initialValue


        // if(scope.ngObject && scope.ngObject.$promise)
        //   scope.ngObject.$promise.then(function(){
        //     init()
        //   });
        // else
        //   init();

        // function init(){
          
        //   scope.$watch('ngModel', function(){
        //     el.change()
        //   });

          

        //   cm = simplemde.codemirror

        //   cm.on('update', function(){
        //     console.log('updating')
        //     console.log(el.val() == simplemde.value())
        //     var value = simplemde.value();
        //     if(el.val() != value){
        //       scope.ngModel = value; // set model
        //       el.val(value);
        //       scope.$apply();
        //     }
        //     // $scope.ngModel = simplemde.value()
        //   });
        //   // cm.on('update', function(){
        //   //   value = simplemde.value()
        //   //   if(el.val() != value){
        //   //     console.log('UPDATE CHANGE')
        //   //     el.val = value;
        //   //     el.change();
        //   //     if(scope.ngObject)
        //   //       scope.ngObject.$dirty = true;
        //   //   }
        //   // });

        //   el.on('change', function(){

        //     // console.log('changed', el.val().length, simplemde.value.length)
        //     value = el.val();
        //     if(simplemde.value() != value){
        //       console.log('changing')
        //       simplemde.value(value);
        //     }
        //   });
        // };

      }
    };
  })