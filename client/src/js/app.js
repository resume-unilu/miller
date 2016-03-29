/**
 * @ngdoc overview
 * @name miller
 * @description
 * # miller
 *
 * Main module of the application.
 */
angular
  .module('miller', [
    'ui.router',
    'ngResource',
    'ngSanitize',
    'ngCookies',
    'angular-medium-editor',
    'mgcrea.ngStrap'
  ])
  .constant('LOCALES', {
    'locales': {
      'en_US': 'English'
    },
    'preferredLocale': 'en_US'
  })
  /*
    Angular-translate configs
    Cfr. https://scotch.io/tutorials/internationalization-of-angularjs-applications
  */
  // .config(function ($translateProvider) {
  //   // $translateProvider.useMissingTranslationHandlerLog();
  //   $translateProvider.useSanitizeValueStrategy('sanitize');
  //   $translateProvider.useStaticFilesLoader({
  //       prefix: 'locale/locale-',// path to translations files
  //       suffix: '.json'// suffix, currently- extension of the translations
  //   });
  //   $translateProvider.preferredLanguage('en_US');// is applied on first load
    
  // })

  .config(function($locationProvider) {
    // $locationProvider.html5Mode(true);
  })
  .config(function ($stateProvider, $urlRouterProvider, RUNTIME) {
    $urlRouterProvider
      .otherwise("/");
    $stateProvider
      .state('index', {
        url: '/',
        controller: 'IndexCtrl',
        templateUrl: RUNTIME.static + 'templates/index.html'
      })
      .state('login', {
        url: '/login',
        controller: 'LoginCtrl',
        templateUrl: RUNTIME.static + 'templates/login.html'
      })
      .state('draft', {
        url: '/create',
        controller: 'DraftCtrl',
        templateUrl: RUNTIME.static + 'templates/draft.html'
      })
      .state('me', {
        abstract: true,
        url: '/me',
        controller: 'MeCtrl',
        templateUrl: RUNTIME.static + 'templates/me.html'
      })
        .state('me.stories', {
          url: '/stories',
          controller: 'ItemsCtrl',
          templateUrl: RUNTIME.static + 'templates/me.stories.html',
          resolve: {
            items: function(StoryFactory) {
              return StoryFactory.get().$promise;
            },
            model: function() {
              return 'story';
            },
            factory: function(StoryFactory) {
              return StoryFactory;
            }
          }
        })
  });
