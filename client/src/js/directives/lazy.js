/**
 * @ngdoc function
 * @name miller.directives:lazy
 * @description
 * # marked
 * transform markdown data in miller enhanced datas
 */
angular.module('miller')
  .directive('lazyImage', function ($log) {
    return {
      restrict : 'A',
      scope: {
        src: '='
      },
      link : function(scope, element, attrs) {
        $log.log(':::lazy on ',scope.src);

        element.addClass('lazy-box').css({
          'background-color': '#B7B2B2',
        }).html('<div class="loading">...</div>');
        
        function wakeup(){
          element.css({
            'background-size': attrs.size || 'cover',
            'background-position': 'center center',
            'background-repeat': 'no-repeat',
            'background-image': 'url(' + scope.src + ')'
          });
          element.find('.loading').hide();
        }

        scope.$watch('src', function(v){
          if(v)
            wakeup(); // or start watching for in page
        });

      }
    };
  })
  /*
    lazy placeholder for document, filled when needed only.
  */
  .directive('lazyPlaceholder', function($log, RUNTIME) {
    return {
      //transclude: true,
      scope:{

      },
      templateUrl: RUNTIME.static + 'templates/partials/document.placeholder.html',
      link : function(scope, element, attrs) {
        var slug = element.attr('lazy-placeholder');
        $log.log(':::lazy-placeholder on ',typeof slug, '--->',slug);
        
        if(scope.$parent.resolve && typeof slug=='string'){
          scope.$parent.resolve(slug, 'doc', function(doc){
            // add to this local scope

            if(doc)
              scope.resolved = doc;
            else 
              $log.error('cannot find', slug );

            $log.log(':::lazy-placeholder resolved: ',scope.resolved);

          })
        }
        
      }
    }
  });