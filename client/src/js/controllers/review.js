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

    
    $scope.fields = [
      'thematic','interest', 'originality', 'innovation', 'interdisciplinarity', 'methodology', 'clarity', 'argumentation','structure', 'references', 'pertinence'];

    $scope.availableStatuses = [
      'draft', 'completed', 'refusal', 'bounce'
    ];


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

      answers.contents = JSON.stringify($scope.review.contents);
      
      answers.status = 'draft';
      
      ReviewFactory.patch({
        id: review.id
      }, answers, function(review){
        $scope.review = review;
        $log.debug('WritingCtrl @SAVE: success');
        $scope.$emit(EVENTS.MESSAGE, 'saved');
        $scope.unlock();
        $scope.isSaving = false;
        $scope.toggleStopStateChangeStart(false);
      }, function(err){
        $log.warn('WritingCtrl @SAVE: error', err);
        $scope.$emit(EVENTS.MESSAGE, 'error!');
        $scope.unlock();
        $scope.isSaving = false;
      })
    };


    $scope.finalize = function(status){
      $log.debug('WritingCtrl @SAVE');
      $scope.$emit(EVENTS.MESSAGE, 'closing the review');
      $scope.lock();
      if($scope.isSaving){
        $log.warn('wait, try again in. Is still saving.')
        return;
      }
      $scope.isSaving = true;

      ReviewFactory.patch({
        id: review.id
      }, {
        status: status // the final status!!!
      }, function(){
        $log.debug('WritingCtrl @SAVE: success');
        
        $scope.unlock();
        $scope.isSaving = false;
      }, function(err){
        $log.warn('WritingCtrl @SAVE: error', err);
        $scope.$emit(EVENTS.MESSAGE, 'Your request cannot be resolved. Is the review submitted already?');
        $scope.unlock();
        $scope.isSaving = false;
      })
    }

    // calculate final score based on fields.
    $scope.$watch('review', function(r, p){
      if(r){
        debugger
        // min points: 
        // var minpoints =  $scope.fields.length,
        $scope.points = _.filter(r, function(d, k){
          return k.indexOf('_score') != -1
        }).reduce(function(a,b){
          return a + b;
        });
        $scope.is_valid = $scope.points >= $scope.fields.length;
        
        // autosave draft
      }
    }, true)

    $scope.review = review;
    $scope.$on(EVENTS.SAVE, $scope.save);
  }); 
  