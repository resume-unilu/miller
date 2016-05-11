/**
 * @ngdoc function
 * @name miller.controller:indexCtrl
 * @description
 * # IndexCtrl
 */
angular.module('miller')
  .controller('IndexCtrl', function ($scope, $log, writings, news) {
    $log.debug('IndexCtrl welcome');

    /*
      Get the firs n sentence until the number of words are covered.
      return an array
    */
    function tokenize(text, words){
      var sentences = text.split(/[\.!\?]/);
      console.log(text, sentences);
      return sentences;
    }

    writings.results = writings.results.map(function(d) {
      d.excerpt = tokenize(d.abstract, 10)[0];
      return d;
    });

    $scope.coverstory = writings.results.shift();
    $scope.otherstories = writings.results;

    $scope.news = news.results.map(function(d) {
      d.excerpt = tokenize(d.abstract, 10)[0];
      return d;
    });



  });
  