/**
 * @ngdoc function
 * @name miller.directives:slidingSteps
 * @description
 * 
 */
angular.module('miller')
  .directive('slidingSteps', function($log, $rootScope, RUNTIME, $timeout){
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
            steps = element.find('.sliding-steps'),
            stepswrapper = steps.parent(),
            stepsHeight = steps[0].offsetHeight,
            stepswrapperHeight = stepswrapper[0].offsetHeight,

            translateY = 0,
            lastIdxSelected;

        scope.user = $rootScope.user;
        
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


        scope.reach = function(idx, sideoffset, refOffset, step){
          stepswrapperHeight = stepswrapper[0].offsetHeight;
          stepsHeight = steps[0].offsetHeight;

          var expectedOffset = (refOffset  - sideoffset),
              visibleOffset = - (sideoffset + step[0].offsetHeight - stepswrapperHeight);

          $log.log('⏣ sliding-steps > reach idx:', idx, 
                   '- side offset:',    sideoffset, 
                   '- ref offset:',     refOffset, 
                   // '- scrollY:',      window.scrollY,
                   '- parentOffset:',   parentOffset,
                   '- expectedOffset:', expectedOffset,
                   '- visibleOffset:',  visibleOffset,
                   '- step[0].offsetHeight: ', step[0].offsetHeight);

          // debugger
          translateY = Math.min(expectedOffset,visibleOffset);
          steps.css('transform', 'translateY(' + translateY  + 'px)');
          scope.isMoreTop =  expectedOffset < -2;
          scope.isMoreBottom = stepsHeight + translateY > stepswrapperHeight;
          
        };


        scope.prev = function() {
          $log.log('⏣ sliding-steps > prev - idx:',lastIdxSelected,
            '- isMoreTop:', scope.isMoreTop);
          if(!scope.isMoreTop)
            return;

          // if(lastIdxSelected > 1){
          //   scope.alignTo(lastIdxSelected);
          //   return;
          // }

          steps.children().each(function(i, d){
            
            // debugger
            
            
            if(d.offsetTop + translateY > 0){
              // debugger
              // break it!
              console.log('...',target);
            
              return false;
            }
            target = +d.id.replace('step-', '');
            
          });

          if(target)
            scope.alignTo(target);
              
          
        };

        scope.next = function() {
          // calculate if there is any step that is below floating line.
          
          $log.log('⏣ sliding-steps > next - idx:',lastIdxSelected,
            '- steps',    steps ) 

          steps.children().each(function(i, d){
            if(i < lastIdxSelected){
              return true;
            }
            console.log('...',(d.offsetTop + d.offsetHeight + translateY),stepswrapperHeight, (d.offsetTop + d.offsetHeight + translateY < stepswrapperHeight));
            // debugger
            if(d.offsetTop + d.offsetHeight + translateY > stepswrapperHeight){
              scope.alignTo(+d.id.replace('step-', ''));
              // debugger
              // break it!
              return false;
            }
            
          });
          
          // steps.css('transform', 'translateY(' + Math.min(expectedOffset,visibleOffset) + 'px)');
          
        };

        /*
          Scope below
        */
        scope.isMoreTop = false;
        scope.isMoreBottom = stepsHeight > stepswrapperHeight;


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
          var item = angular.element('#item-'+idx),
              step = element.find('#step-'+idx);

          sideoffset = _sideOffset || step[0].offsetTop;
          refOffset  = _refOffset || item[0].offsetTop;
          
          // disable if it is the same
          if (lastIdxSelected == idx -1){
            scope.reset(item);
            return;
          }

          if(lastIdxSelected !== undefined){
            scope.items[lastIdxSelected].isFocused = false;
            // console.log('#item-'+lastIdxSelected)
            angular.element('#item-'+(lastIdxSelected+1)).removeClass('active')
          }
          item.addClass('active');
          lastIdxSelected = idx - 1;// idx = 0 does not exist
          scope.items[idx - 1].isFocused = true;
          scope.reach(idx, sideoffset, refOffset, step);
        }

        scope.reset = function(){
          if(lastIdxSelected) {
            scope.items[lastIdxSelected].isFocused = false;
            angular.element('#item-'+(lastIdxSelected+1)).removeClass('active');
            lastIdxSelected = undefined;
          }
        }

        scope.alignTo = function(idx){
          $log.log('⏣ sliding-steps > alignTo -idx:', idx);
          var step = element.find('#step-'+idx);
          sideOffset = step[0].offsetTop;
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
          scope.align(idx,sideOffset,refOffset, step)
        }

        scope.$watch('focus', function(idx){
          if(idx){ // idx = 0 does not exist, cfr services.MarkdownitService
            $log.log('⏣ sliding-steps @focus - idx:', idx, scope.items[idx-1]);
            scope.align(idx);
          } else if(idx === 0) {
            scope.reset();
          }
        })

        $timeout(function() {
          stepsHeight = steps[0].offsetHeight,
          stepswrapperHeight = stepswrapper[0].offsetHeight,
          scope.isMoreBottom = stepsHeight > stepswrapperHeight;
        }, 1000);
      }
    }
  })