/**
 * @ngdoc function
 * @name miller.controller:UploadCtrl
 * @description
 * # UploadCtrl
 * handle story creation via upload.
 */
angular.module('miller')
  .controller('UploadCtrl', function ($scope, $state, $log, Upload, EVENTS) {
    $log.debug('UploadCtrl welcome');
    $scope.uploadable = {
      title: '',
      abstract: ''
    }
    $scope.$watch('docx', function (v) {
      if(v){
        $log.debug('UploadCtrl @docx', v.name, v.size)
        $scope.uploadable.docx = v;
        $scope.uploadable.name = v.name;
        $scope.uploadable.size = v.size;
      }
    });

    $scope.upload = function(){
      $log.debug('UploadCtrl -> upload()');
      if(!$scope.createForm.$valid){
        $log.warn('UploadCtrl -> upload() errors:', $scope.createForm.$error);
        return;
      }
      if(!$scope.uploadable.docx || $scope.uploadable.docx.$error){
        $log.warn('UploadCtrl -> upload() cannot find a valid docx file');
        return;
      }
      Upload.upload({
        url: '/api/story/',
        data: {
          title: $scope.uploadable.title,
          abstract: $scope.uploadable.abstract,
          source: $scope.uploadable.docx
        }
      }).then(function (res) {
        $log.debug('UploadCtrl -> upload() status:', res.status)
        if(res.status == 201){
          $log.debug('UploadCtrl -> upload() status:', 'success!', res.data)
          // location redirect.
          $state.go('uploaded', {
            storyId: res.data.slug
          });
        } else {
          // error handling?
        }

      }, null, function (evt) {
        
          var progressPercentage = parseInt(100.0 *
              evt.loaded / evt.total);
          $log.log('progress: ' + progressPercentage + 
            '% ' + evt.config.data. source.name);
      });
    }
  })