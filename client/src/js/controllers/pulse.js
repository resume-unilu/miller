/**
 * @ngdoc function
 * @name miller.controller:PulseCtrl
 * @description
 * # PulseCtrl
 * socket connection for user notifications.
 * Used directly below CoreCtrl
 */
angular.module('miller')
  .controller('PulseCtrl', function ($scope, $log, RUNTIME) {
    $log.log('⚡ PulseCtrl ready');
    
    var socket = window.socket = new ReconnectingWebSocket('ws://' + window.location.host + '/ws/?session_key=' +  RUNTIME.settings.session_key);

    socket.onmessage = function(e) {
      $log.log('⚡ -> ',e.data, e)
    }

    socket.onopen = function() {
      $log.log('⚡ online');
    }

    socket.onclose = function(e) {
      $log.warn("socket closed.", e);
    }

    socket.onerror = function(e) {
      $log.error("socket error", e);
    }

    // Call onopen directly if socket is already open
    if (socket.readyState == WebSocket.OPEN)
      socket.onopen();
  });
  