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
    // 'ngAnimate',
    'ngResource',
    'ngSanitize',
    'ngCookies',
    'ngTagsInput',
    'mgcrea.ngStrap',
    'monospaced.elastic',
    'LocalStorageModule',
    'pascalprecht.translate',
    // 'angular-embedly',
    'ngDisqus',
    'angular-embed',
    'angular-embed.handlers'
  ])
  .constant('LOCALES', {
    'locales': {
      'en_US': 'English'
    },
    'preferredLocale': 'en_US'
  })
  .constant('EVENTS', {
    'SAVE': 'save',
    'MESSAGE': 'message',
    'BAD_REQUEST':'bad_request',
    // namespace for markdownit directive
    'MARKDOWNIT_FULLSIZE': 'markdownit_fullsize'
  })
  /*
    disqus configuration
  */
  .config(function($disqusProvider, RUNTIME) {
    if(RUNTIME.settings.disqus){
      $disqusProvider.setShortname(RUNTIME.settings.disqus);
    }

  })
  /*
    prefix
  */
  .config(function($locationProvider) {
    $locationProvider.hashPrefix('!');
  })
  /*
    multiple input tags configuration
  */
  .config(function(tagsInputConfigProvider, RUNTIME) {
    tagsInputConfigProvider
    .setDefaults('tagsInput', {
      replaceSpacesWithDashes:false,
      template: RUNTIME.static + 'templates/partials/tag.input.html' 
    })
    .setDefaults('autoComplete', {
      loadOnDownArrow: true
    });
  })
  /*
    Angular-translate configs
    Cfr. https://scotch.io/tutorials/internationalization-of-angularjs-applications
  */
  .config(function ($translateProvider, RUNTIME) {
    // $translateProvider.useMissingTranslationHandlerLog();
    $translateProvider.useSanitizeValueStrategy('sanitize');
    $translateProvider.useStaticFilesLoader({
        prefix: RUNTIME.static + 'locale/locale-',// path to translations files
        suffix: '.json'// suffix, currently- extension of the translations
    });
    $translateProvider.preferredLanguage('en_US');// is applied on first load
    
  })
  .config(function (localStorageServiceProvider) {
    localStorageServiceProvider
      .setPrefix('miller');
  })
  .config(function($resourceProvider) {
    $resourceProvider.defaults.stripTrailingSlashes = false;
  })
  .config(function($httpProvider) {
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';

    // intercept BAD request errors
    $httpProvider.interceptors.push(function($q, $rootScope, EVENTS) {
      return {
        responseError: function(rejection) {
          // emit on 400 error (bad request, mostly form errors)
          if(rejection.status == 400){
            $rootScope.$emit(EVENTS.BAD_REQUEST, rejection);
          }
          return $q.reject(rejection);
        }
      };
    });
  })
  .config(function($locationProvider) {
    // $locationProvider.html5Mode(true);
  })
  .config(function(embedlyServiceProvider, RUNTIME) {
    if(RUNTIME.oembeds.EMBEDLY_API_KEY)
      embedlyServiceProvider.setKey(RUNTIME.oembeds.EMBEDLY_API_KEY);
  })
  .config(function ($stateProvider, $urlRouterProvider, RUNTIME) {
    $urlRouterProvider
      .otherwise("/");
    $stateProvider
      .state('index', {
        url: '/',
        reloadOnSearch : false,
        controller: 'IndexCtrl',
        templateUrl: RUNTIME.static + 'templates/index.html',
        resolve:{
          writings: function(StoryFactory){
            return StoryFactory.get({
              filters: JSON.stringify({
                tags__slug: 'highlights'
              })
            }).$promise;
          },
          news: function(StoryFactory){
            return StoryFactory.get({
              filters: JSON.stringify({
                tags__category: 'blog'
              })
            }).$promise;
          } 
        }
      })
      .state('authors', {
        url: '/authors',
        reloadOnSearch : false,
        controller: 'ItemsCtrl',
        templateUrl: RUNTIME.static + 'templates/authors.html',
        resolve: {
          items: function(ProfileFactory, $stateParams) {
            return ProfileFactory.get({
              // filters: JSON.stringify({
              //   status: 'draft',
              //   owner__username: RUNTIME.user.username,
              //   // authors__username__in: [RUNTIME.user.username]
              // })
            }).$promise;
          },
          model: function() {
            return 'profile';
          },
          factory: function(ProfileFactory) {
            return ProfileFactory;
          }
        }
      })
      .state('login', {
        url: '/login',
        reloadOnSearch : false,
        controller: 'LoginCtrl',
        templateUrl: RUNTIME.static + 'templates/login.html'
      })
      .state('draft', {
        url: '/create',
        reloadOnSearch : false,
        controller: 'DraftCtrl',
        templateUrl: RUNTIME.static + 'templates/draft.html'
      })
      .state('writing', {
        url: '/writing/:storyId',
        reloadOnSearch : false,
        controller: 'WritingCtrl',
        templateUrl: RUNTIME.static + 'templates/draft.html',
        resolve: {
          story: function(StoryFactory, $stateParams) {
            return StoryFactory.get({id: $stateParams.storyId}).$promise;
          },
        }
      });

    /*

      My stories, settings etc. (even drafts whenever available)
      ---
    
    */
    $stateProvider
      .state('me', {
        abstract: true,
        reloadOnSearch : false,
        url: '/me',
        controller: 'AuthorCtrl',
        templateUrl: RUNTIME.static + 'templates/author.html',
        resolve: {
          profile: function(ProfileFactory, RUNTIME){
            return ProfileFactory.get({
              username: RUNTIME.user.username
            }).$promise;
          }
        }
      })
      .state('me.publications', {
        url: '/publications',
        abstract:true,
        reloadOnSearch : false,
        controller: function($scope){
          $scope.urls = RUNTIME.stories.writing;
        },
        templateUrl: RUNTIME.static + 'templates/author.publications.html',
      })
      .state('me.publications.drafts', {
        url: '/drafts',
        reloadOnSearch : false,
        controller: 'ItemsCtrl',
        templateUrl: RUNTIME.static + 'templates/items.html',
        resolve: {
          items: function(StoryFactory, $stateParams) {
            return StoryFactory.get({
              filters: JSON.stringify({
                status: 'draft',
                owner__username: RUNTIME.user.username,
                // authors__username__in: [RUNTIME.user.username]
              })
            }).$promise;
          },

          model: function() {
            return 'story';
          },
          factory: function(StoryFactory) {
            return StoryFactory;
          }
        }
      });

      _.each(RUNTIME.stories.writing, function(d){
        $stateProvider
          .state('me.publications.' + d.name, {
            url: d.url,
            controller: 'ItemsCtrl',
            templateUrl: RUNTIME.static + 'templates/items.html',
              resolve: {
              items: function(StoryFactory, $stateParams) {
                return StoryFactory.get({
                  filters: d.slug? JSON.stringify({
                    tags__category: 'writing',
                    tags__slug: d.slug,
                    owner__username: RUNTIME.user.username
                  }): JSON.stringify({
                    tags__category: 'writing',
                    owner__username: RUNTIME.user.username
                  })
                }).$promise;
              },

              model: function() {
                return 'story';
              },
              factory: function(StoryFactory) {
                return StoryFactory;
              }
            }
          });
      });

    /*
      Other user stories
      ---
    */
    $stateProvider
      .state('author', {
        abstract: true,
        reloadOnSearch : false,
        url: '/author/{username:[0-9a-zA-Z\\.-_]+}',
        controller: 'AuthorCtrl',
        templateUrl: RUNTIME.static + 'templates/author.html',
        resolve: {
          profile: function(ProfileFactory, $stateParams){
            return ProfileFactory.get({
              username: $stateParams.username
            }).$promise;
          }
        }
      })
      .state('author.publications', {
        url: '',
        reloadOnSearch : false,
        controller: function($scope, profile){
          $scope.urls = RUNTIME.stories.writing;
        },
        resolve:{ // latest stories
          stories: function(profile){
            return {'value': profile};
          }
        },
        templateUrl: RUNTIME.static + 'templates/author.publications.html',
      });

      

    $stateProvider
     .state('blog', {
        url: '/blog',
        reloadOnSearch : false,
        abstract:true,
        controller: 'BlogCtrl',
        templateUrl: RUNTIME.static + 'templates/blog.html',
        
      })

      .state('blog.everything', {
        url: '',
        reloadOnSearch : false,
        controller: 'ItemsCtrl',
        templateUrl: RUNTIME.static + 'templates/items.html',
        resolve: {
          items: function(StoryFactory, $stateParams) {
            return StoryFactory.get({
              filters: JSON.stringify({
                tags__category: 'blog'
              })
            }).$promise;
          },
          model: function() {
            return 'story';
          },
          factory: function(StoryFactory) {
            return StoryFactory;
          }
        }
      })
      .state('blog.events', {
        url: '/events',
        reloadOnSearch : false,
        controller: 'ItemsCtrl',
        templateUrl: RUNTIME.static + 'templates/items.html',
        resolve: {
          items: function(StoryFactory, $stateParams) {
            return StoryFactory.get({
              filters: JSON.stringify({
                tags__category: 'blog',
                tags__slug: 'event'
              })
            }).$promise;
          },
          model: function() {
            return 'story';
          },
          factory: function(StoryFactory) {
            return StoryFactory;
          }
        }
      })
      
      // .state('events', {
      //   url: '/events',
      //   abstract:true,
      //   reloadOnSearch : false,
      //   // controller: function(){},
      //   templateUrl: RUNTIME.static + 'templates/events.html',
        
      // })

      // .state('events.everything', {
      //   url: '',
      //   controller: 'ItemsCtrl',
      //   reloadOnSearch : false,
      //   templateUrl: RUNTIME.static + 'templates/items.html',
      //   resolve: {
      //     items: function(StoryFactory, $stateParams) {
      //       return StoryFactory.get({
      //         filters: JSON.stringify({
      //           tags__category: 'event'
      //         })
      //       }).$promise;
      //     },
      //     model: function() {
      //       return 'story';
      //     },
      //     factory: function(StoryFactory) {
      //       return StoryFactory;
      //     }
      //   }
      // })

      /*
        Kind of story:writings publications
      */
      .state('publications', {
        url: '/publications',
        abstract: true,
        reloadOnSearch : false,
        controller: function($scope){
          $scope.urls = RUNTIME.stories.writing;
        },
        templateUrl: RUNTIME.static + 'templates/publications.html',
        
      })

      _.each(RUNTIME.stories.writing, function(d){
        $stateProvider
          .state('publications.' + d.name, {
            url: d.url,
            controller: 'ItemsCtrl',
            templateUrl: RUNTIME.static + 'templates/items.html',
              resolve: {
              items: function(StoryFactory, $stateParams) {
                return StoryFactory.get({
                  filters: d.slug? JSON.stringify({
                    tags__category: 'writing',
                    tags__slug: d.slug
                  }): JSON.stringify({
                    tags__category: 'writing'
                  })
                }).$promise;
              },

              model: function() {
                return 'story';
              },
              factory: function(StoryFactory) {
                return StoryFactory;
              }
            }
          });
      });
      
      
      


    $stateProvider
      .state('story', {
        url: '/story/:postId',
        controller: 'StoryCtrl',
        reloadOnSearch : false,
        templateUrl: RUNTIME.static + 'templates/story.html',
        resolve: {
          story: function(StoryFactory, $stateParams) {
            return StoryFactory.get({id: $stateParams.postId}).$promise;
          },
        }
      })


      /*
        All the rest are static pages and will download the md files directly
      */
      .state('page', {
        url: '/:name',
        controller: 'PageCtrl',
        templateUrl: RUNTIME.static + 'templates/md.html',
        resolve: {
          page: function(PageFactory, $stateParams) {
            return PageFactory.get({name: $stateParams.name});
          },
        }
      });
  });
