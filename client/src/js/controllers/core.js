/**
 * @ngdoc function
 * @name miller.controller:coreCtrl
 * @description
 * # CoreCtrl
 * common functions go here.
 */
angular.module('miller')
  .controller('CoreCtrl', function ($rootScope, $scope, $log, $location, $anchorScroll, localStorageService, $translate, $timeout, StoryFactory, TagFactory, RUNTIME, EVENTS) {
    $log.log('\n    oila!   \n(-(-_(-_-)_-)-)\n\n\n');
    
    $log.log('CoreCtrl ready, user:', RUNTIME.user.username, RUNTIME);

    $scope.user = RUNTIME.user;

    $scope.hasToC = false;
    $scope.ToCEnabled = false;

    $scope.toggleTableOfContents = function() {
      $scope.hasToC = !$scope.hasToC;
    };

    $scope.locationPath = '';

    $scope.setToC = function(ToC) {
      $log.log('CoreCtrl > setToC data:', ToC);
      $scope.ToC = ToC;
      // $scope.ToCEnabled = false;
    };

    $scope.disableToC = function(){
      $scope.ToCDisabled = true
    }

    // add document items to the table-of)documents
    $scope.setDocuments = function(documents) {
      $log.log('CoreCtrl > setDocuments items n.:', documents.length);
      $scope.documents = documents;
    };

    $scope.save = function(){
      $log.log('CoreCtrl > @SAVE ...'); 
      $scope.$broadcast(EVENTS.SAVE);
    }

    $scope.update = function(key, value){
      $log.log('CoreCtrl > @UPDATE ',key,':',value,' ...'); 
      var _d = {};
      _d[key] = value;
      $scope.$broadcast(EVENTS.UPDATE, _d);
    }


    $scope.lock = function(){
      $log.log('CoreCtrl > lock .............'); 
      
    }

    $scope.unlock = function(){
      $log.log('CoreCtrl > unlock .............'); 
      
    }

    /*
      Suggest tags for writing purposes
    */
    $scope.suggestTags = function(query, options) {
      $log.log('CoreCtrl -> suggestTags', query, options);
      var filters = options || {}
      return TagFactory.get({
        filters: JSON.stringify(filters)
      }).$promise.then(function(response) {
        return response.results
      })
    }
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

    $scope.changeLanguage = function(key) {
      $scope.language = key;
      localStorageService.set('lang', $scope.language)
      $translate.use(key);
    }
    /*
      On location change, collect the parameters.
      Since this is called BEFORE statehangeSuccess, the scrolling cannot be made at this level.
    */
    $scope.$on('$locationChangeSuccess', function (e, path) {
      $log.debug('CoreCtrl @locationChangeSuccess', path);
      $scope.qs = $location.search();
      $scope.locationPath = path;
    });


    /*
      First load
    */
    // load language
    $scope.language = localStorageService.get('lang') || 'en_US';
    $scope.changeLanguage($scope.language);
    // load "huighlights"
    StoryFactory.get({
      filters: JSON.stringify({
        tags__category: 'highlights'
      })
    }, function(data){
      $log.info('CoreCtrl breaking news loaded', data)
      $scope.setBreakingNews(data.results)
    }); 



  });
  