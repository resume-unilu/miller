/**
 * @ngdoc function
 * @name miller.controller:CollectionCtrl
 * @description
 * # CollectionCtrl
 * transfor a story having tag collection in something completely crazy
 */
angular.module('miller')
  .controller('CollectionCtrl', function($scope, $log, collection, EVENTS, StoryFactory){
    $log.log('CollectionCtrl ready', $scope.user.username)


    $scope.collection = collection;
    $scope.collection.isWritable = $scope.hasWritingPermission($scope.user, $scope.collection);

    // set status DRAFT or PUBLIC to the document.
    $scope.setStatus = function(status){
      $log.debug('CollectionCtrl -> setStatus - status:', status);
      
      if(!$scope.user.is_staff)
        return;
        
      $scope.$emit(EVENTS.MESSAGE, 'saving');

      // yep, a collection is still a story
      StoryFactory.update({
        id: $scope.collection.id
      }, {
        title: $scope.collection.title,
        status: status
      }, function(res) {
        $scope.collection.status = res.status;
        $scope.$emit(EVENTS.MESSAGE, 'saved');
        $scope.unlock();
      });
    }

  })