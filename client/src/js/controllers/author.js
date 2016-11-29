/**
 * @ngdoc function
 * @name miller.controller:MeCtrl
 * @description
 * # MeCtrl
 * common functions go here.
 */
angular.module('miller')
  .controller('AuthorCtrl', function ($scope, $log, author) {
    $scope.isMe = $scope.user.username == author.profile.username;
    $log.log('AuthorCtrl ready, author:',author.fullname);
    $scope.author = author;

  })
  .controller('AuthorEditCtrl', function ($scope, $state, $log, AuthorFactory, author, EVENTS) {
    $log.log('AuthorEditCtrl ready, author:', author, $scope.previousState);
    $scope.author = author;
    $scope.isSaving = false;

    $scope.save = function(){
      $log.log('AuthorEditCtrl -> save()', $scope.author);
      if($scope.isSaving){
        $log.warn('wait, try again in. Is still saving.')
        return
      }
      $scope.isSaving = true;
      AuthorFactory.patch({
        slug: $scope.author.id, // let's use the standard id for patch. This way we shouldn't change the default viewset
      },{
        fullname: [$scope.author.metadata.firstname,$scope.author.metadata.lastname].join(' '),
        metadata:  JSON.stringify($scope.author.metadata),
        affiliation: $scope.author.affiliation
      }, function(res) {
        // $log.log('ok:',res)
        $scope.$emit(EVENTS.MESSAGE, 'saved');
        $scope.isSaving = false;
        
        if($scope.previousState.from && $scope.previousState.from.name && $scope.previousState.from.name.length)
          $state.go($scope.previousState.from.name, $scope.previousState.fromParams)
        else
          $state.go('author.publications.all', {slug: $scope.author.slug})
      }, function(err) {
        $log.error('error:', err.data);
        $scope.isSaving = false;
      })
    }
    
  });
  