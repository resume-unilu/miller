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
  .directive('footnote', function(){
    return {
      restrict : 'A',
      scope:{
        caption: '=',
        footnote: '=',
      },
      template: '<span class="footnote"><a ng-click="toggleFootnote()">{{caption}}</a><div class="footnote-contents" ng-show="isOpened">rr</div></span>',
      link: function(scope, element, attrs) {
        var footnoteSl = '#fn'+scope.caption + ' p', // footnote jquery selector
            contents = element.find('.footnote-contents');

        scope.isOpened = false;

        scope.toggleFootnote = function(){
          scope.isOpened = !scope.isOpened;
          if(scope.isOpened && !scope.isFilled){
            $(contents).html($(footnoteSl).clone())
            scope.isFilled = true;
          }
        }
      }
    }
  })
  .directive('markdownit', function ($compile, $log, $location, markdownItService) {
    return {
      restrict : 'A',
      scope:{
        markdownit: '=',
        settoc: '&',
        setdocs: '&',
        language: '='
      },
      link : function(scope, element, attrs) {
        var entities = [],
            annotable = false,
            
            ToC = [],
            docs = [],
            footnotes = {};

        scope.hash = function(what) {
          $location.hash(what);
        };
        
        
        function parse() {
          if(!scope.markdownit || !scope.markdownit.length){
            $log.warn(':: markdownit parse() without any markdown text! Check the value for `markdownit`');
            return;
          }
          var results  = markdownItService(scope.markdownit, scope.language);

          element.html(results.html);
          $compile(element.contents())(scope);
          if(scope.settoc)
            scope.settoc({ToC:results.ToC});
          if(scope.setdocs)
            scope.setdocs({items:results.docs});
        };

        // watch language and reparse everything when needed.
        if(scope.language)
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