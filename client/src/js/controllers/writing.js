/**
 * @ngdoc function
 * @name miller.controller:WritingCtrl
 * @description
 * # DraftCtrl
 * handle saved story writing ;)
 */
angular.module('miller')
  .controller('WritingCtrl', function ($scope, $log, $modal, story, localStorageService, StoryFactory, StoryTagsFactory, DocumentFactory, EVENTS, RUNTIME) {
    $log.debug('WritingCtrl welcome', story);

    $scope.isDraft = false;
    $scope.isSaving = false;

    $scope.title = story.title
    $scope.abstract = story.abstract
    $scope.contents = story.contents
    $scope.keywords = _.filter(story.tags, {category: 'keyword'});

    $scope.displayedTags = _.filter(story.tags, function(d){
      return d.category != 'keyword'
    });

    $scope.metadata = {
      status: story.status,
      owner: story.owner
    }

    $scope.setStatus = function(status) {
      $scope.metadata.status = status;
      $scope.save();
    }

    $scope.references = [];
    $scope.lookups = [];// ref and docs and urls...

    // atthach the tag $tag for the current document.
    $scope.attachTag = function(tag) {
      $log.debug('WritingCtrl -> attachTag() tag', arguments);
      $scope.isSaving = true;
      $scope.lock();
      return StoryFactory.patch({id: story.id}, {
        tags: _.map($scope.displayedTags, 'id')
      }).$promise.then(function(res) {
        $log.debug('WritingCtrl -> attachTag() tag success', res);
        $scope.unlock();
        $scope.isSaving =false;
        return true
      }, function(){
        // error
        return false
      });
    }

    $scope.detachTag = function(tag) {
      $log.debug('WritingCtrl -> detachTag() tag', arguments, $scope.displayedTags);
      $scope.isSaving = true;
      $scope.lock();
      
      return StoryFactory.patch({id: story.id}, {
        tags: _.map($scope.displayedTags, 'id')
      }).$promise.then(function(res) {
        $log.debug('WritingCtrl -> detachTag() tag success', res);
        $scope.unlock();
        $scope.isSaving =false;
        return true
      }, function(){
        // error
        return false
      });
    }

    $scope.suggestReferences = function(service) {
      if(!service)
        DocumentFactory.get(function(){
          console.log('list')
        })
    }
    

    $scope.save = function() {
      $log.debug('WritingCtrl @SAVE');
      $scope.isSaving = true;
      $scope.lock();
      StoryFactory.update({id: story.id}, angular.extend({
        title: $scope.title,
        abstract: $scope.abstract,
        contents: $scope.contents
      }, $scope.metadata), function(res) {
        console.log(res)
        $scope.unlock();
        $scope.isSaving =false;
      })
    };

    $scope.$on(EVENTS.SAVE, $scope.save);

    $scope.$watch('contents', function(v){
      console.log('changed contents')
    })
  });
  
