/**
 * @ngdoc function
 * @name miller.controller:DraftCtrl
 * @description
 * # DraftCtrl
 * handle draft writing ;)
 */
angular.module('miller')
  .controller('DraftCtrl', function ($scope, $log, $state, localStorageService, StoryFactory, EVENTS) {
    $log.debug('DraftCtrl welcome');
    
    $scope.isSaving = false;

    $scope.save = function(){
      $log.log('DraftCtrl -> save()')
      if($scope.isSaving){
        $log.warn(' .. is still saving, be patient.')
        return;
      }

      $scope.isSaving = true;
      
      StoryFactory.save({}, {
        title: $scope.title,
        abstract: $scope.abstract,
        contents: '',
        status: 'draft'
      }, function(res) {
        $scope.isSaving = false;
        $scope.$emit(EVENTS.MESSAGE, 'saved');
        $log.log('DraftCtrl -> @EVENTS.SAVE saved:', res);
        // handle redirection.
        $state.go('writing', {
          storyId: res.slug
        });
        // debugger
      }, function(err){
        $log.error(err)
        $scope.isSaving = false;
      });
    };
    
    $scope.$on(EVENTS.SAVE, function() {
      $scope.$emit(EVENTS.MESSAGE, 'saving');
      $scope.save();
    });
  });
  