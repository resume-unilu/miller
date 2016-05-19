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
  });