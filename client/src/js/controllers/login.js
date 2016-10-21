/**
 * @ngdoc function
 * @name miller.controller:LoginCtrl
 * @description
 * # LoginCtrl
 * login!
 */
angular.module('miller')
  .controller('LoginCtrl', function ($scope, $log, AuthFactory, $location) {
    $log.log('👉 LoginCtrl ready');

    $scope.login = function(){
      $log.debug('👉 LoginCtrl > login');
      if($scope.pwd && $scope.pwd.length && $scope.username &&  $scope.username){
        AuthFactory.login({
          username: $scope.username,
          password: $scope.pwd
        }, function(res){
          
          $location.url('/');
        }, function(err){
          $log.error('👉 LoginCtrl > login error:', err.data);
        });
      }
    }
  });
  