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
        
        element.html(marked(scope.markdown));
        $compile(element.contents())(scope);
      }
    }
  })
  .directive('marked', function ($compile, $log, $location) {
   return {
      restrict : 'A',
      scope:{
        marked: '=',
        settoc: '&',
        setdocs: '&'
      },
      link : function(scope, element, attrs) {
        var entities = [],
            renderer = new marked.Renderer(),
            annotable = false,
            ToC = [],
            docs = [],
            lp; // previous opened heading level, for ToC purposes
        
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

        scope.hash = function(what) {
          $location.hash(what)
        };

        scope.miller = function(url){
          debugger
        }
        /*
          render headings with anchor links and fill the ToC. once everything is rendered, the ToC is sent to the proper function
        */
        renderer.heading = function(text, level){
          // toc is empty
          var h = {
            text: text,
            level: level,
            slug: slugify(text)
          };
          ToC.push(h);
          return '<h' + level + '><div class="anchor-sign" ng-click="hash(\''+ h.slug +'\')"><span class="icon-link"></span></div><a name="' + h.slug +'" class="anchor" href="#' + h.slug +'"><span class="header-link"></span></a>' +
                  text + '</h' + level + '>';
        }


        renderer.link = function(url, boh, text) {
          if(url.trim().indexOf('doc:') == 0){
            // collect document
            var documents = url.trim().replace('doc:','').split(',');

            for(var i in documents){
              docs.push({
                citation: text,
                slug: documents[i]
              });
            }
            
            return '<a name="' + documents[0] +'" ng-click="hash(\''+url+'\')"><span class="anchor-wrapper"></span>'+text+'</a>';
          }

          return '<a href>'+text+'</a>'
        }

        element.html(marked(scope.marked, {
          renderer: renderer
        }));


        
        $compile(element.contents())(scope);

        scope.settoc({ToC:ToC});
        if(scope.setdocs)
          scope.setdocs({items:docs})
      }
    };
  })