/**
 * @ngdoc function
 * @name miller.controller:CollectionCtrl
 * @description
 * # CollectionCtrl
 * transfor a story having tag collection in something completely crazy
 */
angular.module('miller')
  .controller('CollectionCtrl', function($scope, $rootScope, $log, collection, EVENTS, StoryFactory, markdownItChaptersService){
    $log.log('CollectionCtrl ready', $scope.user.username, $scope.language)


    $scope.collection = collection;
    
    $scope.collection.isWritable = $scope.hasWritingPermission($scope.user, $scope.collection);

    // get cover of collection
    if(collection.covers.length){
      $scope.collection.cover = _.first(collection.covers);
    }

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

    var links = markdownItChaptersService(collection.contents, $scope.language);
    var stories = _.keyBy(collection.stories, 'slug');
    
    // filter chapters from links
    $scope.chapters = links.map(function(d){
      if(stories[d.slug]){
        return stories[d.slug]
      }
      return d;
    })

    
  })