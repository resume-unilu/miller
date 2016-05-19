/**
 * @ngdoc function
 * @name miller.directives:marked
 * @description
 * # marked
 * transform markdown data in miller enhanced datas
 */
angular.module('miller')
  .directive('markdown', function($compile, $log, $location){
    return {
      restrict : 'A',
      scope:{
        markdown: '=',
      },
      link : function(scope, element, attrs) {
        if(scope.markdown && scope.markdown.length) {
          element.html(marked(scope.markdown));
          $compile(element.contents())(scope);
        }
      }
    };
  })
  .directive('markedLanguage', function($compile, $log, $location){
    return {
      restrict : 'A',
      scope:{
        markedLanguage: '=',
      },
      link : function(scope, element, attrs) {
        if(scope.markdown && scope.markdown.length) {
          element.html(marked(scope.markdown));
          $compile(element.contents())(scope);
        }
      }
    };
  })
  .directive('marked', function ($compile, $log, $location, markedService) {
   return {
      restrict : 'A',
      scope:{
        marked: '=',
        settoc: '&',
        setdocs: '&',
        language: '='
      },
      link : function(scope, element, attrs) {
        var entities = [],
            renderer = new marked.Renderer(),

            annotable = false,
            ToC = [],
            docs = [],
            lp; // previous opened heading level, for ToC purposes

        scope.hash = function(what) {
          $location.hash(what);
        };

        scope.miller = function(url){
          // ?
        };
        
        function init(){
          if(!scope.marked || !scope.marked.length){
            $log.warn(':: marked init(), no text to be marked');
            return;
          }
          var rendered  = markedService(scope.marked, scope.language);

          element.html(rendered.html);
          $compile(element.contents())(scope);
          if(scope.settoc)
            scope.settoc({ToC:rendered.ToC});
          if(scope.setdocs)
            scope.setdocs({items:rendered.docs});
        }

        

        if(scope.language)
          scope.$watch('language', function(language){
            if(language)
              init();
          });
        else
          init();
      }
    };
  });