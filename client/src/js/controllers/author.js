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
    $log.log('AuthorEditCtrl ready, author:', author.fullname);
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
        username: $scope.author.id,
      },{
        fullname: [$scope.author.metadata.firstname,$scope.author.metadata.lastname].join(' '),
        metadata:  JSON.stringify($scope.author.metadata),
        affiliation: $scope.author.affiliation
      }, function(res) {
        // $log.log('ok:',res)
        $scope.$emit(EVENTS.MESSAGE, 'saved');
        $scope.isSaving = false;
        $state.go('author.publications.all', {username: $scope.author.profile.username})
      }, function(err) {
        $log.error('error:', err.data);
        $scope.isSaving = false;
      })
    }
    
  });
  