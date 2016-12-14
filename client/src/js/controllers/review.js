/**
 * @ngdoc function
 * @name miller.controller:PulseCtrl
 * @description
 * # PulseCtrl
 * socket connection for user notifications.
 * Used directly below CoreCtrl
 */
angular.module('miller')
  .controller('ReviewCtrl', function ($scope, $log, review, ReviewFactory, RUNTIME, EVENTS) {
    $log.log('⏱ ReviewCtrl ready');

    $scope.review = review;

    $scope.fields = [
      'thematic','interest', 'originality', 'innovation', 'interdiciplinarity', 'methodology', 'clarity', 'argumentation','structure', 'references', 'pertincence'];


    $scope.save = function(){
      $log.debug('WritingCtrl @SAVE');
      $scope.$emit(EVENTS.MESSAGE, 'saving');
      $scope.lock();
      if($scope.isSaving){
        $log.warn('wait, try again in. Is still saving.')
        return
      }
      $scope.isSaving = true;

      answers = {}
      // remap: we patch object only for some fields.
      for(s in $scope.fields){
        var field = $scope.fields[s];
        answers[field] = $scope.review[field]
        answers[field + '_score'] = $scope.review[field + '_score'] || 0
      }
      
      ReviewFactory.patch({
        id: review.id
      }, answers, function(review){
        $scope.review = review;
        $log.debug('WritingCtrl @SAVE: success');
        $scope.$emit(EVENTS.MESSAGE, 'saved');
        $scope.unlock();
        $scope.isSaving = false;

      }, function(err){
        $log.warn('WritingCtrl @SAVE: error', err);
        $scope.$emit(EVENTS.MESSAGE, 'error!');
        $scope.unlock();
        $scope.isSaving = false;
      })
    };

    $scope.$on(EVENTS.SAVE, $scope.save);
  }); 
  