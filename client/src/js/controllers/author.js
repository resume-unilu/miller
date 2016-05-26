/**
 * @ngdoc function
 * @name miller.controller:MeCtrl
 * @description
 * # MeCtrl
 * common functions go here.
 */
angular.module('miller')
  .controller('AuthorCtrl', function ($scope, $log, profile) {
    $scope.isMe = $scope.user.username == profile.username;
    $scope.profile = profile;
    $log.log('AuthorCtrl ready, user:', $scope.user, profile);
    
  });
  