/**
 * @ngdoc function
 * @name miller.controller:coreCtrl
 * @description
 * # CoreCtrl
 * common functions go here.
 */
angular.module('miller')
  .controller('CoreCtrl', function ($rootScope, $scope, $log, $location, $anchorScroll, $timeout, StoryFactory, RUNTIME) {
    $log.log('\n    oila!   \n(-(-_(-_-)_-)-)\n\n\n');
    
    $log.log('CoreCtrl ready, user:', RUNTIME.user.username, RUNTIME);

    $scope.user = RUNTIME.user;

    $scope.hasToC = false;
    $scope.ToCEnabled = false;

    $scope.toggleTableOfContents = function() {
      $scope.hasToC = !$scope.hasToC;
    };

    $scope.setToC = function(ToC) {
      $log.log('CoreCtrl > setToC data:', ToC);
      $scope.ToC = ToC;
      $scope.ToCEnabled = false;
    };

    $scope.disableToC = function(){
      $scope.ToCDisabled = true
    }

    // add document items to the table-of)documents
    $scope.setDocuments = function(documents) {
      $log.log('CoreCtrl > setDocuments items n.:', documents.length);
      $scope.documents = documents;
    };

    /*
      Set breaking news above the header.
      Cfr indexCtrl
    */
    $scope.breakingNews = [];
    $scope.setBreakingNews = function(breakingNews) {
      $scope.breakingNews = breakingNews;
    }

    $rootScope.$on('$stateChangeStart', function (e, state) {
      $log.log('CoreCtrl @stateChangeStart', state);
    })

    $rootScope.$on('$stateChangeSuccess', function (e, state) {
      var h =  $location.hash();

      $log.debug('CoreCtrl @stateChangeSuccess', state.name, h);

      // clean
      $scope.ToC = [];
      $scope.documents = []

      // the ui.router state (cfr app.js)
      $scope.state = state.name;
      $timeout($anchorScroll, 0); // wait for the next digest cycle (cfr marked directive)



    });


    $scope.setHash = function(hash) {
      $location.hash(hash);
    }
    /*
      On location change, collect the parameters.
      Since this is called BEFORE statehangeSuccess, the scrolling cannot be made at this level.
    */
    $scope.$on('$locationChangeSuccess', function (e, path) {
      $log.debug('CoreCtrl @locationChangeSuccess', path);
      $scope.qs = $location.search();

    });

    /*
      First load
    */
    StoryFactory.get({
      filters: JSON.stringify({
        tags__category: 'highlights'
      })
    }, function(data){
      $log.info('CoreCtrl breaking news loaded', data)
      $scope.setBreakingNews(data.results)
    }); 

  });
  