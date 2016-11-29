/**
 * @ngdoc function
 * @name miller.directives:embedit
 * @description
 * # embedit
 * allows embedding of html. 
 * If an object and a language are provided, it handles the translation.
 */
angular.module('miller')
  .directive('embedit', function($sce) {
    return {
      restrict : 'A',
      scope:{
        embedit: '=',
        stretch: '=',
        language: '=',
        firstline: '='
      },
      link: function(scope, element, attrs) {
        // console.log('::embedit @link, language:', scope.language, scope.embedit)
        var options = {
          breaks:       true,
          linkify:      true,
        }, 
        disable = ['image', 'heading'];

        scope.render = function(language) {
          if(!scope.embedit)
            return;
          
          if(language && typeof scope.embedit == 'object') {
            
            var altlanguage = scope.language.replace(/_[A-Z][A-Z]$/, ''),
                contents = scope.embedit[language]||scope.embedit[altlanguage]||'';


            if(attrs.markdown){
              var md = new window.markdownit(options)
                .disable(disable);

              contents = md.render(contents)
            }
            
            if(scope.firstline)
              contents = contents.split(/<br\s?\/?>/).shift();
            
            element.html(contents);
          } else if(attrs.markdown){
            var md = new window.markdownit(options)
              .disable(disable);
            contents = md.render(scope.embedit)
            element.html(contents);
          } else {
            element.html(scope.embedit)
          }

          if(scope.stretch){
            element.find('iframe').width('100%').height('100%');
          }
        };
        

        // enable listeners
        if(scope.language && typeof scope.embedit == 'object') {
          scope.$watch('language', scope.render);
        } else{
          scope.render();
        }

        // if(attrs.watch)
        //   scope.$watch('embedit', function(obj){
        //     if(obj)
        //       scope.render
        //   });
      }
    }
  });