/**
 * @ngdoc function
 * @name miller.controller:coreCtrl
 * @description
 * # CoreCtrl
 * common functions go here.
 */
angular.module('miller')
  .controller('ItemsCtrl', function ($scope, $log, items, model, factory) {
    $log.log('ItemsCtrl ready', items);

    /*
      Get the firs n sentence until the number of words are covered.
      return an array
    */
    function tokenize(text, words){
      var sentences = text.split(/[\.!\?]/);
      // console.log(text, sentences);
      return sentences;
    }

    $scope.items = items.results.map(function(d){
      if(!d.abstract)
        return d;
      var sentences = tokenize(d.abstract, 10);

      d.excerpt = sentences.shift();

      if(sentences.length)
        d.difference = sentences.join('. ');

      return d;
    });

  });
  