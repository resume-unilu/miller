/**
 * @ngdoc function
 * @name miller.directives:marked
 * @description
 * # marked
 * transform markdown data in miller enhanced datas
 */
angular.module('miller')
  .directive('footnote', function($compile){
    return {
      restrict : 'A',
      scope:{
        caption: '=',
        footnote: '='
      },
      require: "^?markdownit",
      template: '<span class="footnote"><a ng-click="toggleFootnote()" style="cursor:pointer">{{caption}}</a><div class="footnote-contents" ng-show="isOpened"></div></span>',
      link: function(scope, element, attrs) {
        var footnoteSl = '#fn'+scope.caption + ' p', // footnote jquery selector
            contents = $(footnoteSl).clone(),
            wrapper = element.find('.footnote-contents');
        
        

        wrapper.html(contents);
        $compile(wrapper.contents())(scope);
        
        scope.isOpened = false;

        scope.toggleFootnote = function(){
          console.log('::footnote > toggleFootnote')
          scope.isOpened = !scope.isOpened;
          // if(scope.isOpened && !scope.isFilled){
            
          //   scope.isFilled = true;
          // }
        }

        scope.fullsize = function(slug, type){
          scope.$parent.fullsize(slug, type);
        }

      }
    }
  })
  .directive('embedit', function($sce){
    return {
      restrict : 'A',
      scope:{
        embedit: '=',
        stretch: '=',
        language: '=',
        firstline: '='
      },
      link: function(scope, element, attrs){
        // console.log('::embedit @link, language:', scope.language)
        if(scope.language && typeof scope.embedit == 'object'){
          var altlanguage = scope.language.replace(/_[A-Z][A-Z]$/, '');
          
          if(scope.firstline){
            element.html((scope.embedit[scope.language]||scope.embedit[altlanguage]||'').split(/<br\/?>/).shift());
          } else {
            element.html(scope.embedit[scope.language]||scope.embedit[altlanguage]||'');
          }
        } else {
          element.html(scope.embedit);
        }
        if(scope.stretch){
          element.find('iframe').width('100%').height('100%');
        }

        // enable listeners
        if(scope.language && typeof scope.embedit == 'object'){
          scope.$watch('language', function(language){
            if(typeof scope.embedit == 'object'){
              element.html(scope.embedit[scope.language]|| '');
            }
          })
        }
      }
    }
  })
  // .directive('hold', function($log, $rootScope, $compile, RUNTIME){
  //   return {
  //     restrict : 'A',
  //     scope: {
  //     },
  //     templateUrl: RUNTIME.static + 'templates/partials/hold.html',
  //     link : function(scope, element, attrs) {
  //       $log.log(':: hold ready')

  //       scope.language = ''+scope.$parent.language;
        
  //       var doc =  _.find(scope.$parent.resources, {
  //         slug: attrs.slug,
  //         _type: attrs.type
  //       });

  //       if(!doc){
  //         $log.error(':: hold: cannot find the document or the glossary term specified by attrs:', attrs);
  //         return;
  //       }

  //       $rootScope.resolve(doc.slug, attrs.type, function(res){
  //         $log.log(':: hold received:', res)

  //         scope.resource = res;
  //         // scope.$apply()
  //         $compile(element.contents())(scope);
  //       })
        
  //     }
  //   }
  // })
  // main markdown directive, almost always used
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
            
            ToC = [],
            docs = [],
            footnotes = {};

        scope.hash = function(what) {
          $location.hash(what);
        };

        scope.focus = function(idx) {
          $log.log(':: markdownit > focus - idx:', idx);
          if(scope.listener){
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