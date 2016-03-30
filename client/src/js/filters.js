angular.module('miller')
  .filter('prefixTemplate', function (RUNTIME) {
    return function (input) {
      return RUNTIME.static + input;
    };
  });