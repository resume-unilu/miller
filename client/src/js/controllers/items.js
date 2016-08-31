/**
 * @ngdoc function
 * @name miller.controller:coreCtrl
 * @description
 * # CoreCtrl
 * common functions go here.
 */
angular.module('miller')
  .controller('ItemsCtrl', function ($scope, $log, items, model, factory, QueryParamsService) {
    $log.log('ItemsCtrl ready, n.:', items.count, '- items:',items);

    /*
      Get the firs n sentence until the number of words are covered.
      return an array
    */
    function tokenize(text, words){
      var sentences = text.split(/[\.!\?]/);
      // console.log(text, sentences);
      return sentences;
    }

    function normalizeItems(items) {
      return items
        .map(function(d){
          if(!d.abstract)
            return d;
          var sentences = tokenize(d.abstract, 10);

          d.excerpt = sentences.shift();

          if(sentences.length)
            d.difference = sentences.join('. ');

          return d;
        })
    };
    
    // update scope vars related to count, missing, and render the items
    $scope.sync = function(res){
      $scope.isLoadingNextItems = false;
      // update next
      next = QueryParamsService(res.next || '');
      console.log('ItemsCtrl > sync()', next);
      // update count
      $scope.count = res.count;
      // push items
      $scope.items = ($scope.items || []).concat(normalizeItems(res.results));
      // update missing
      $scope.missing = res.count - $scope.items.length;
    }

    $scope.more = function(){
      if($scope.isLoadingNextItems){
        $log.warn('is still loading');
        return;
      }
      $scope.isLoadingNextItems = true;
      factory.get(next, $scope.sync);
    }

    $scope.sync(items);
    
  });
  