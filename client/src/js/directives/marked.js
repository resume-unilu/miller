/**
 * @ngdoc function
 * @name miller.directives:marked
 * @description
 * # marked
 * transform markdown data in miller enhanced datas
 */
angular.module('miller')
  .directive('markdownit', function ($compile, $log, $location, markdownItService, EVENTS) {
    return {
      restrict : 'A',
      scope:{
        markdownit: '=',
        settoc: '&',
        setdocs: '&',
        language: '=',
        watchlanguage: '=',
        listener: '&',

      },
      link : function(scope, element, attrs) {
        var entities = [],
            annotable = false,
            previousFocus,
            ToC = [],
            docs = [],
            footnotes = {};

        scope.hash = function(what) {
          $location.hash(what);
        };

        scope.focus = function(idx) {
          $log.log(':: markdownit > focus - idx:', idx);
          if(previousFocus && previousFocus == idx && scope.listener){
            previousFocus = 0;
            // unfocus @todo. id = 0 works but i not the best solution.
            scope.listener({
              event: EVENTS.MARKDOWNIT_FOCUS, 
              data: {
                idx: 0
              }
            });
          } else if(scope.listener){
            previousFocus = idx;
            scope.listener({
              event: EVENTS.MARKDOWNIT_FOCUS, 
              data: {
                idx: idx
              }
            });
            
          }

        }

        scope.fullsize = function(slug, type){
          if(scope.listener){
            scope.listener({
              event: EVENTS.MARKDOWNIT_FULLSIZE, 
              data: {
                slug: slug.replace(/^[^\/]*\//, ''),
                type: type
              }
            });
          }
        }

        scope.resolve = function(slug, type, notify){
          if(scope.listener){
            scope.listener({
              event: EVENTS.MARKDOWNIT_RESOLVE, 
              data: {
                slug: slug,
                type: type
              },
              callback: notify
            });
          }
        }
        
        function parse() {
          if(!scope.markdownit || !scope.markdownit.length){
            $log.warn(':: markdownit parse() without any markdown text! Check the value for `markdownit`');
            return;
          }
          var results  = markdownItService(scope.markdownit, scope.language);


          scope.resources = results.docs

          element.html(results.html);
          $compile(element.contents())(scope);
          if(scope.settoc)
            scope.settoc({ToC:results.ToC});
          if(scope.setdocs)
            scope.setdocs({items:results.docs});
          
        };

        // watch language and reparse everything when needed.
        if(scope.watchlanguage && scope.language)
          scope.$watch('language', function(language){
            if(language)
              parse();
          });
        else
          parse();
      }
    }
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