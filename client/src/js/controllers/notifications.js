/**
 * @ngdoc function
 * @name miller.controller:PulseCtrl
 * @description
 * # PulseCtrl
 * socket connection for user notifications.
 * Used directly below CoreCtrl
 */
angular.module('miller')
  .controller('NotificationsCtrl', function ($scope, $log, RUNTIME) {
    $log.log('⏱ NotificationsCtrl ready');
  });
  