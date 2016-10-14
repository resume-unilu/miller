/**
 * @ngdoc function
 * @name miller.directives:marked
 * @description
 * # marked
 * clone markdownit footnote in the place you like.
 * Cfr footnote template.
 */
angular.module('miller')
  .directive('footnote', function($compile, RUNTIME){
    return {
      restrict : 'A',
      scope:{
        caption: '=',
        footnote: '='
        
      },
      templateUrl: RUNTIME.static + 'templates/partials/directives/footnote.html',
      // require: "^?markdownit",
      
      link: function(scope, element, attrs) {
        var footnoteSl = '#fn'+ scope.footnote + ' p', // footnote jquery selector
            contents = $(footnoteSl).clone(),
            wrapper = element.find('.footnote-contents');

        wrapper.html(contents);
        $compile(wrapper.contents())(scope);
       
        scope.isOpened = !!attrs.isOpened;

        scope.toggleFootnote = function(){
          console.log('::footnote > toggleFootnote')
          // scope.isOpened = !scope.isOpened;
          // if(scope.isOpened && !scope.isFilled){
            
          //   scope.isFilled = true;
          // }
        }

        scope.fullsize = function(slug, type){
          if(scope.$parent.fullsize) {
            scope.$parent.fullsize(slug, type);
          } else {
            $log.error(":: footnote > fullsize is without hanlders.");
          }
        }

      }
    }
  });