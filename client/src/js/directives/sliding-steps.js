/**
 * @ngdoc function
 * @name miller.directives:slidingSteps
 * @description
 * 
 */
angular.module('miller')
  .directive('slidingSteps', function($log, $rootScope, RUNTIME){
    return {
      restrict : 'A',
      scope: {
        items: '=',
        focus: '=',
        language: '='
      },
      templateUrl: RUNTIME.static + 'templates/partials/directives/sliding-steps.html',
      link : function(scope, element, attrs) {
        $log.log('⏣ sliding-steps ready, items.length:', _.map(scope.items, '_index'), scope.items.length, scope.items);
        var sideOffset = 0,
            refOffset = 0,
            parentOffset = element.offset().top,
            
            lastIdxSelected;

        // basic request animationframe shim
        var requestAnimFrame = (function(){
          return  window.requestAnimationFrame || window.webkitRequestAnimationFrame || window.mozRequestAnimationFrame || function( callback ){ window.setTimeout(callback, 1000 / 60); };
        })();

        var easeInOutQuad = function (t, b, c, d) {
          t /= d/2;
          if (t < 1) {
            return c/2*t*t + b
          }
          t--;
          return -c/2 * (t*(t-2) - 1) + b;
        };

        function scrollTo(to, callback, duration) {
          // because it's so fucking difficult to detect the scrolling element, just move them all
          function move(amount) {
            document.documentElement.scrollTop = amount;
            document.body.parentNode.scrollTop = amount;
            document.body.scrollTop = amount;
          }
          function position() {
            return document.documentElement.scrollTop || document.body.parentNode.scrollTop || document.body.scrollTop;
          }
          var start = position(),
            change = to - start,
            currentTime = 0,
            increment = 20;
          duration = (typeof(duration) === 'undefined') ? 360 : duration;
          var animateScroll = function() {
            // increment the time
            currentTime += increment;
            // find the value with the quadratic in-out easing function
            var val = easeInOutQuad(currentTime, start, change, duration);
            // move the document.body
            move(val);
            // do the animation unless its over
            if (currentTime < duration) {
              requestAnimFrame(animateScroll);
            } else {
              if (callback && typeof(callback) === 'function') {
                // the animation is done so lets callback
                callback();
              }
            }
          };
          animateScroll();
        }


        function reach(idx, sideoffset, refOffset){
          $log.log('⏣ sliding-steps > reach idx:', idx, 
                   '- side offset:',  sideoffset, 
                   '- ref offset:',   refOffset, 
                   // '- scrollY:',      window.scrollY,
                   '- parentOffset:', parentOffset);

          element.css('transform', 'translateY(' + (refOffset  - sideoffset) + 'px)');
        };

        scope.fullsize = function(slug, type){
          $log.log('⏣ sliding-steps > fullsize slug:', slug);
          $rootScope.fullsize(slug, type);
        };
  //       $rootScope.resolve(doc.slug, attrs.type, function(res){
  // //         $log.log(':: hold received:', res)

  // //         scope.resource = res;
  // //         // scope.$apply()
  // //         $compile(element.contents())(scope);
  // //       })

        //
        // increase or decrease the translation value for the silly thing. 
        scope.align = function(idx, _sideOffset, _refOffset) {
          var item = angular.element('#item-'+idx);

          sideoffset = _sideOffset || element.find('#step-'+idx)[0].offsetTop;
          refOffset  = _refOffset || item[0].offsetTop;
          

          if(lastIdxSelected !== undefined){
            scope.items[lastIdxSelected].isFocused = false;
            // console.log('#item-'+lastIdxSelected)
            angular.element('#item-'+(lastIdxSelected+1)).removeClass('active')
          } 
          item.addClass('active');
          lastIdxSelected = idx - 1;// idx = 0 does not exist
          scope.items[idx - 1].isFocused = true;
          reach(idx, sideoffset, refOffset);
        }

        scope.alignTo = function(idx, evt){
          $log.log('⏣ sliding-steps > alignTo -idx:', idx, '- clientY:', evt.clientY);
          sideOffset = element.find('#step-'+idx)[0].offsetTop;
          refOffset  = angular.element('#item-'+idx)[0].offsetTop;
          
          var wrapperOffset = element.parent().offset().top;
          
          // do the scrolling now. calculate where the scrolling should be then.
          // ideally, refOffset should reach side offset
          // scope.align(idx, sideoffset, refOffset);
          $log.log('⏣ sliding-steps > alignTo idx:', idx, 
                   '- side offset:',  sideOffset, 
                   '- ref offset:',   refOffset, 
                   // '- scrollY:',      window.scrollY,
                   '- win height:', window.innerHeight/3,
                   '- parentOffset:', parentOffset,
                   '- current scrollY:', window.scrollY);

          scrollTo(refOffset + wrapperOffset - window.innerHeight/2)
          scope.align(idx,sideOffset,refOffset)
        }

        // on destroy
        scope.$watch('focus', function(idx){
          if(idx){ // idx = 0 does not exist, cfr services.MarkdownitService
            $log.log('⏣ sliding-steps @focus - idx:', idx, scope.items[idx-1]);
            scope.align(idx);
            
          }
        })
      }
    }
  })