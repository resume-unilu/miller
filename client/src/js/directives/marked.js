/**
 * @ngdoc function
 * @name miller.directives:marked
 * @description
 * # marked
 * transform markdown data in miller enhanced datas
 */
angular.module('miller')
  .directive('marked', function ($compile, $log, $location) {
   return {
      restrict : 'A',
      scope:{
        marked: '=',
        settoc: '&'
      },
      link : function(scope, element, attrs) {
        var entities = [],
            renderer = new marked.Renderer(),
            annotable = false,
            ToC = [],
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



        element.html(marked(scope.marked, {
          renderer: renderer
        }));


        
        $compile(element.contents())(scope);

        scope.settoc({ToC:ToC});
      }
    };
  })