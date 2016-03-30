/**
 * @ngdoc function
 * @name miller.controller:coreCtrl
 * @description
 * # CoreCtrl
 * common functions go here.
 */
angular.module('miller')
  .controller('CoreCtrl', function ($rootScope, $scope, $log, RUNTIME) {
    $log.log('CoreCtrl ready, user:', RUNTIME.user.username, RUNTIME);

    $scope.user = RUNTIME.user;

    $scope.hasToC = false;

    $scope.toggleTableOfContents = function() {
      $scope.hasToC = !$scope.hasToC;
    };

    /*
      Set breaking news above the header.
      Cfr indexCtrl
    */
    $scope.breakingNews = [];
    $scope.setBreakingNews = function(breakingNews) {
      $scope.breakingNews = breakingNews;
    }

    $rootScope.$on('$stateChangeStart', function (e, state) {
      $log.log('CoreCtrl @stateChangeStart', state);
    })

    $rootScope.$on('$stateChangeSuccess', function (e, state) {
      $log.debug('CoreCtrl @stateChangeSuccess', state.name);
      // the ui.router state (cfr app.js)
      $scope.state = state.name;
    });

  });
  