/**
 * @ngdoc function
 * @name miller.controller:coreCtrl
 * @description
 * # CoreCtrl
 * common functions go here.
 */
angular.module('miller')
  .controller('CoreCtrl', function ($rootScope, $scope, $log, $location, $anchorScroll, $modal, $alert, localStorageService, $translate, $timeout, StoryFactory, TagFactory, RUNTIME, EVENTS) {    
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
      $scope.ToCDisabled = true;
    };

    // add document items to the table-of)documents
    $scope.setDocuments = function(documents) {
      $log.log('CoreCtrl > setDocuments items n.:', documents.length, documents);
      $scope.documents = documents;
      if($scope.qs.view) {
        // check if it's somewhere in the scope, otherwise callit
        for(var i=0,j=$scope.documents.length;i<j;i++){
          if($scope.qs.view == $scope.documents[i].short_url){
            $scope.fullsized = $scope.documents[i];
            fullsizeModal.$promise.then(fullsizeModal.show);
            break;
          }
        }
      };
    };

    $scope.save = function(){
      $log.log('CoreCtrl > @SAVE ...'); 
      $scope.$broadcast(EVENTS.SAVE);
    };

    $scope.update = function(key, value){
      $log.log('CoreCtrl > @UPDATE ',key,':',value,' ...'); 
      var _d = {};
      _d[key] = value;
      $scope.$broadcast(EVENTS.UPDATE, _d);
    };


    $scope.lock = function(){
      $log.log('CoreCtrl > lock .............'); 
      
    };

    $scope.unlock = function(){
      $log.log('CoreCtrl > unlock .............'); 
      
    };

    /*
      Suggest tags for writing purposes
    */
    $scope.suggestTags = function(query, options) {
      $log.log('CoreCtrl -> suggestTags', query, options);
      var filters = options || {};
      return TagFactory.get({
        filters: JSON.stringify(filters)
      }).$promise.then(function(response) {
        return response.results;
      });
    };
    /*
      Set breaking news above the header.
      Cfr indexCtrl
    */
    $scope.breakingNews = [];
    $scope.setBreakingNews = function(breakingNews) {
      $scope.breakingNews = breakingNews;
    };

    $rootScope.$on('$stateChangeStart', function (e, state) {
      $log.log('CoreCtrl @stateChangeStart new:', state.name, '- previous:', $scope.state);
      // for specific state only.

      if($scope.state && ['draft', 'writing'].indexOf($scope.state) !== -1){
        // check the user has wirtten sometihing..
        var answer = confirm("Are you sure you want to leave this page?")
        if (!answer) {
            e.preventDefault();
        }
      }
    });

    $rootScope.$on('$stateChangeSuccess', function (e, state) {
      var h =  $location.hash();

      $log.debug('CoreCtrl @stateChangeSuccess', state.name, h);

      // clean
      $scope.ToC = [];
      $scope.documents = [];

      // the ui.router state (cfr app.js)
      $scope.state = state.name;
      $timeout($anchorScroll, 0); // wait for the next digest cycle (cfr marked directive)




    });


    $scope.setHash = function(hash) {
      $location.hash(hash);
    };

    $scope.changeLanguage = function(key) {
      $scope.language = key;
      localStorageService.set('lang', $scope.language);
      $translate.use(key);
    };


    /*
      When requested, fullsize for documents.
      Cfr also locationChangeSuccess listener 
    */
    var fullsizeModal = $modal({
      scope: $scope, 
      template: RUNTIME.static + 'templates/partials/modals/fullsize.html',
      id: 'dii',
      show: false
    });
    
    $scope.$on('modal.hide', function(e,modal){
      if(modal.$id== 'dii')
        $location.search('view', null);
    });

    $scope.fullsize = function(doc) {
      $log.log('CoreCtrl -> fullsize', doc);
      $scope.fullsized = doc;
      $location.search('view', doc.short_url);
    };


    /*
      Prevent from closing
    */
    window.onbeforeunload = function (event) {
      if($scope.state && ['draft', 'writing'].indexOf($scope.state) !== -1){
        var message = 'Sure you want to leave?';
        if (typeof event == 'undefined') {
          event = window.event;
        }
        if (event) {
          event.returnValue = message;
        }
        return message;
      }
    }

    /*
      On location change, collect the parameters.
      Since this is called BEFORE statehangeSuccess, the scrolling cannot be made at this level.
    */
    $scope.$on('$locationChangeSuccess', function (e, path) {
      $log.debug('CoreCtrl @locationChangeSuccess', path, $location);
      $scope.qs = $location.search();
      $scope.locationPath = path;
      $scope.path = $location.path();

      if($scope.qs.view && $scope.fullsized && $scope.fullsized.short_url == $scope.qs.view){
        // normal behaviour, after fullsize has been called the view param is present in location
        fullsizeModal.$promise.then(fullsizeModal.show);
      }
    });

    // watch 400 bad request form error. Cfr app.js interceptors.
    $rootScope.$on(EVENTS.BAD_REQUEST, function(e, rejection){
      $alert({
        placement: 'top',
        title: 'form errors', 
        'animation': 'bounceIn',
        content: _(rejection.data).map(function(d,k){
          return '<div><b>'+k+'</b>: '+d+'</div>';
        }).value().join(''),
        show: true, 
        type:'error'
      });
    });

    var timer_event_message;
    // watch for saving or MESSAGE events
    $scope.$on(EVENTS.MESSAGE, function (e, message) {
      $log.log('CoreCtrl @MESSAGE', message);
      $scope.message = message;
      if(timer_event_message)
        $timeout.cancel(timer_event_message);
      timer_event_message = $timeout(function(){
        $scope.message = null;
      }, 2000);
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
      $log.info('CoreCtrl breaking news loaded', data);
      $scope.setBreakingNews(data.results);
    }); 



  });
  