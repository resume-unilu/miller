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
    // 'ngDisqus',
    'angular-embed',
    'angular-embed.handlers',
    'angularLoad',
    'angularLazyImg',
    'ngFileUpload',
    '720kb.socialshare'
  ])
  .constant('LOCALES', {
    'locales': {
      'en_US': 'English'
    },
    'preferredLocale': 'en_US'
  })
  .constant('EVENTS', {
    'SAVE': 'save',
    'DOWNLOAD': 'download',
    'MESSAGE': 'message',
    'BAD_REQUEST':'bad_request',
    'PERMISSION_DENIED':'permission_denied',
    'RESIZED': 'resized',
    // namespace for markdownit directive
    'MARKDOWNIT_FULLSIZE': 'markdownit_fullsize',
    'MARKDOWNIT_RESOLVE': 'markdownit_resolve',
    'MARKDOWNIT_FOCUS': 'markdownit_focus',
  })
  /*
    disqus configuration
  */
  // .config(function($disqusProvider, RUNTIME) {
  //   if(RUNTIME.settings.disqus){
  //     $disqusProvider.setShortname(RUNTIME.settings.disqus);
  //   }

  // })
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
    // $httpProvider.defaults.xsrfCookieName = 'Miller';
    // $httpProvider.defaults.xsrfHeaderName = 'HTTP_X_CSFRTOKEN';
    $httpProvider.defaults.xsrfCookieName = 'Miller';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    // intercept BAD request errors
    $httpProvider.interceptors.push(function($q, $rootScope, EVENTS) {
      return {
        responseError: function(rejection) {
          // emit on 400 error (bad request, mostly form errors)
          if(rejection.status == 400){
            $rootScope.$emit(EVENTS.BAD_REQUEST, rejection);
            debugger
          } else if(rejection.status == 403){
            $rootScope.$emit(EVENTS.PERMISSION_DENIED, rejection);
            debugger
          }
          return $q.reject(rejection);
        }
      };
    });
  })
  .config(function($locationProvider) {
    $locationProvider.html5Mode({
      enabled: true,
      requireBase: false,
      rewriteLinks: false
    });
    // $locationProvider.hashPrefix('!');
  })
  .config(function(embedlyServiceProvider, RUNTIME) {
    if(RUNTIME.oembeds.EMBEDLY_API_KEY)
      embedlyServiceProvider.setKey(RUNTIME.oembeds.EMBEDLY_API_KEY);
  })
  .config(function ($stateProvider, $urlRouterProvider, RUNTIME) {
    // $urlRouterProvider.config({
    //   absolute: true
    // })
    $urlRouterProvider
      .otherwise("/");

    $stateProvider
      .state('notfound', {
        url: '/not-found',
        controller: function($log){
          $log.warn('requested page not found.')
        },
        templateUrl: RUNTIME.static + 'templates/index.html',
      });

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
                tags__slug: 'highlights',
                status: 'public'
              }),
              limit: 7,
              ordering: '-date'
            }).$promise;
          },
          news: function(StoryFactory){
            return StoryFactory.get({
              filters: JSON.stringify({
                tags__category: 'blog',
                status: 'public'
              }),
              ordering: '-date'
            }).$promise;
          } 
        }
      })
      .state('index.signup', {
        url: '/',
        reloadOnSearch : false,
        controller: 'SignupCtrl',
        templateUrl: RUNTIME.static + 'templates/signup.html'
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
            return ProfileFactory.get;
          }
        }
      })
      // .state('login', {
      //   url: '/login',
      //   reloadOnSearch : false,
      //   controller: 'LoginCtrl',
      //   templateUrl: RUNTIME.static + 'templates/login.html'
      // })
      .state('draft', {
        url: '/create',
        reloadOnSearch : false,
        controller: 'DraftCtrl',
        templateUrl: RUNTIME.static + 'templates/draft.html'
      })
      .state('upload', {
        url: '/upload',
        reloadOnSearch : false,
        controller: 'UploadCtrl',
        templateUrl: RUNTIME.static + 'templates/upload.html'
      })
      .state('uploaded', {
        url: '/uploaded/:storyId',
        reloadOnSearch : false,
        controller: 'UploadedCtrl',
        templateUrl: RUNTIME.static + 'templates/uploaded.html',
        resolve: {
          story: function(StoryFactory, $stateParams) {
            return StoryFactory.get({id: $stateParams.storyId}).$promise;
          },
        }
      })
      .state('writing', {
        url: '/writing/:storyId',
        reloadOnSearch : false,
        controller: 'WritingCtrl',
        templateUrl: RUNTIME.static + 'templates/writings.html',
        resolve: {
          story: function(StoryFactory, $stateParams) {
            return StoryFactory.get({id: $stateParams.storyId}).$promise;
          },
        }
      });

    /*

      Author routes.
    
    */
    $stateProvider
      .state('author', {
        abstract: true,
        reloadOnSearch : false,
        url: '/author/{slug:[0-9a-zA-Z\\.\\-_]+}',
        controller: 'AuthorCtrl',
        templateUrl: RUNTIME.static + 'templates/author.html',
        resolve: {
          author: function(AuthorFactory, $stateParams){
            return AuthorFactory.get({
              slug: $stateParams.slug
            }).$promise;
          }
        }
      })

      .state('author.publications', {
        url: '/publications',
        abstract:true,
        reloadOnSearch : false,
        controller: function($scope){
          $scope.urls = RUNTIME.stories.writing;
        },
        templateUrl: RUNTIME.static + 'templates/author.publications.html',
      })
      .state('author.publications.drafts', {
        url: '/drafts',
        reloadOnSearch : false,
        controller: 'ItemsCtrl',
        templateUrl: RUNTIME.static + 'templates/items.html',
        resolve: {
          items: function(StoryFactory, author) {
            return StoryFactory.get({
              filters: JSON.stringify({
                status: 'draft',
                authors__slug: author.slug
              }),
              ordering: '-date,-date_last_modified'
            }).$promise;
          },

          model: function() {
            return 'story';
          },
          factory: function(StoryFactory) {
            return StoryFactory.get;
          }
        }
      })
      .state('author.publications.bin', {
        url: '/bin',
        reloadOnSearch : false,
        controller: 'ItemsCtrl',
        templateUrl: RUNTIME.static + 'templates/items.html',
        resolve: {
          items: function(StoryFactory, author) {
            return StoryFactory.get({
              filters: JSON.stringify({
                status: 'deleted',
                authors__slug: author.slug
              }),
              ordering: '-date,-date_last_modified'
            }).$promise;
          },

          model: function() {
            return 'story';
          },
          factory: function(StoryFactory) {
            return StoryFactory.get;
          }
        }
      })
      .state('author.publications.all', {
        url: '/',
        reloadOnSearch : false,
        controller: 'ItemsCtrl',
        templateUrl: RUNTIME.static + 'templates/items.html',
        resolve: {
          items: function(StoryFactory, author) {
            return StoryFactory.get({
              filters: JSON.stringify({
                authors__slug: author.slug
              }),
              ordering: '-date,-date_last_modified'
            }).$promise;
          },

          model: function() {
            return 'story';
          },
          factory: function(StoryFactory) {
            return StoryFactory.get;
          }
        }
      });

      _.each(RUNTIME.stories.writing, function(d){
        $stateProvider
          .state('author.publications.' + d.slug, {
            url: d.url,
            controller: 'ItemsCtrl',
            templateUrl: RUNTIME.static + 'templates/items.html',
              resolve: {
              items: function(StoryFactory, $stateParams, author) {
                return StoryFactory.get({
                  filters: d.slug? JSON.stringify({
                    tags__category__in: ['writing', 'blog'],
                    tags__slug: d.slug,
                    authors__slug: author.slug
                  }): JSON.stringify({
                    tags__category__in: ['writing', 'blog'],
                    authors__slug: author.slug
                  }),
                  ordering: '-date,-date_last_modified'
                }).$promise;
              },

              model: function() {
                return 'story';
              },
              factory: function(StoryFactory) {
                return StoryFactory.get;
              }
            }
          });
      });

    $stateProvider
      .state('modifyauthor', {
        url: '/author/{slug:[0-9a-zA-Z\\.\\-_]+}/edit',
        controller: 'AuthorEditCtrl',
        templateUrl: RUNTIME.static + 'templates/author.edit.html',
        resolve: {
          author: function(AuthorFactory, $stateParams){ 
            return AuthorFactory.get({
              slug: $stateParams.slug
            }).$promise;
          }
        }
      });

    /*
      Profile. One profile per user, that's easier.
    */
    $stateProvider
      .state('profile', {
        // abstract: true,
        url: '/profile/{username:[0-9a-zA-Z\\.\\-_]+}',
        controller: 'ProfileCtrl',
        templateUrl: RUNTIME.static + 'templates/profile.html',
        reloadOnSearch : false,
        resolve: {
          profile: function(ProfileFactory, $stateParams){
            return ProfileFactory.get({
              username: $stateParams.username
            }).$promise;
          },
          authors: function(ProfileFactory, $stateParams){
            return ProfileFactory.authors({
              username: $stateParams.username
            }).$promise;
          },
        }
      })
        .state('profile.publications', {
          url: '/publications',
          reloadOnSearch : false,
          controller: 'ItemsCtrl',
          templateUrl: RUNTIME.static + 'templates/items.html',
          resolve: {
            items: function(StoryFactory, profile, $location) {
              var qs = $location.search()
              
              return StoryFactory.get({
                filters: JSON.stringify({
                  authors__user__username: profile.username
                }),
                ordering: '-date,-date_last_modified'
              }).$promise;
            },
            model: function() {
              return 'story';
            },
            factory: function(StoryFactory) {
              return StoryFactory.get;
            }
          }
        });

    $stateProvider
      .state('reviews', {
        abstract: true,
        url: '/reviews',
        controller: function(){},
        templateUrl: RUNTIME.static + 'templates/reviews.html',
        reloadOnSearch : false,
      })
      .state('reviews.all', {
        url: '',
        controller: 'ItemsCtrl',
        templateUrl: RUNTIME.static + 'templates/items.html',
          resolve: {
          items: function(ReviewFactory, $stateParams) {
            return ReviewFactory.get().$promise;
          },
          model: function() {
            return 'review';
          },
          factory: function(ReviewFactory) {
            return ReviewFactory.get;
          }
        }
      })
      .state('reviews.pending', {
          url: '/pending',
          controller: 'ItemsCtrl',
          templateUrl: RUNTIME.static + 'templates/items.html',
            resolve: {
            items: function(ReviewFactory, $stateParams) {
              return ReviewFactory.get({
                filters: JSON.stringify({
                  status__in: ['initial', 'draft']
                })
              }).$promise;
            },

            model: function() {
              return 'review';
            },
            factory: function(ReviewFactory) {
              return ReviewFactory.get;
            }
          }
        })
      .state('reviews.reports', {
        url: '/reports',
        controller: 'ItemsCtrl',
        templateUrl: RUNTIME.static + 'templates/items.html',
          resolve: {
          items: function(ReviewFactory, $stateParams) {
            return ReviewFactory.reports().$promise;
          },
          model: function() {
            return 'report';
          },
          factory: function(ReviewFactory) { // get items
            return ReviewFactory.reports;
          }
        }
      });

    $stateProvider
      .state('review', {
        url: '/review/{id:[0-9]+}',
        controller: 'ReviewCtrl',
        templateUrl: RUNTIME.static + 'templates/review.html',
        resolve: {
          review: function(ReviewFactory, $stateParams) {
            return ReviewFactory.get({
              id: $stateParams.id
            }).$promise;
          }
        }
      })
      .state('review.story', {
        url: '/story',
        controller: 'StoryCtrl',
        templateUrl: RUNTIME.static + 'templates/story.html',
        resolve: {
          story: function(review) {
            return review.story;
          },
        }
      });
    // report of review.
    $stateProvider
      .state('report', {
        url: '/report/{id:[0-9]+}',
        controller: 'ReviewCtrl',
        templateUrl: RUNTIME.static + 'templates/review.html',
        resolve: {
          review: function(ReviewFactory, $stateParams) {
            return ReviewFactory.report({
              id: $stateParams.id
            }).$promise;
          }
        }
      })

    $stateProvider
     .state('blog', {
        url: '/blog',
        reloadOnSearch : false,
        abstract:true,
        controller: 'BlogCtrl',
        templateUrl: RUNTIME.static + 'templates/blog.html',
        
      })

      
      .state('blog.event', {
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
              }),
              ordering: '-date,-date_last_modified'
            }).$promise;
          },
          model: function() {
            return 'story';
          },
          factory: function(StoryFactory) {
            return StoryFactory.get;
          }
        }
      })
      .state('blog.news', {
        url: '/news',
        reloadOnSearch : false,
        controller: 'ItemsCtrl',
        templateUrl: RUNTIME.static + 'templates/items.html',
        resolve: {
          items: function(StoryFactory, $stateParams) {
            return StoryFactory.get({
              filters: JSON.stringify({
                tags__category: 'blog',
                tags__slug: 'news'
              }),
              ordering: '-date,-date_last_modified'
            }).$promise;
          },
          model: function() {
            return 'story';
          },
          factory: function(StoryFactory) {
            return StoryFactory.get;
          }
        }
      })
      
    

      /*
        Kind of story:writings publications
      */
      .state('publications', {
        url: '/publications',
        abstract: true,
        reloadOnSearch : false,
        controller: function($scope, $state){
          $scope.urls = RUNTIME.stories.writing;
          
          if($state.params.slug)
            $scope.slug = $state.params.slug;
        },
        templateUrl: RUNTIME.static + 'templates/publications.html',
        
      })
        .state('publications.all', {
          url: '',
          controller: 'ItemsCtrl',
          templateUrl: RUNTIME.static + 'templates/items.html',
          resolve: {
            items: function(StoryFactory) {
              return StoryFactory.get({
                filters: JSON.stringify({
                  tags__category: 'writing'
                }),
                exclude:JSON.stringify({
                  tags__slug: 'chapter'
                }),
                ordering: '-date,-date_last_modified'
              }).$promise;
            },

            model: function() {
              return 'story';
            },
            factory: function(StoryFactory) {
              return StoryFactory.get;
            }
          }
        })
        .state('publications.tags', {
          url: '/tags/:slug',
          controller: 'ItemsCtrl',
          templateUrl: RUNTIME.static + 'templates/items.html',
          resolve: {
            items: function(StoryFactory, $stateParams) {
              return StoryFactory.get({
                filters: JSON.stringify({
                  tags__slug: $stateParams.slug
                }),
                ordering: '-date,-date_last_modified'
              }).$promise;
            },

            model: function() {
              return 'story';
            },
            factory: function(StoryFactory) {
              return StoryFactory.get;
            }
          }
        });

      _.each(RUNTIME.stories.writing, function(d){
        $stateProvider
          .state('publications.' + d.slug, {
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
                  }),
                  ordering: '-date,-date_last_modified'
                }).$promise;
              },

              model: function() {
                return 'story';
              },
              factory: function(StoryFactory) {
                return StoryFactory.get;
              }
            }
          });
      });

    $stateProvider
      .state('search', {
        url: '/search?q&tags&authors',
        controller: 'SearchCtrl',
        reloadOnSearch : false,
        templateUrl: RUNTIME.static + 'templates/search.html',
        resolve: {
          items: function(StoryFactory, $location) {
            var qs = $location.search()
            // transform filters keywords in using a service
            return StoryFactory.search(qs).$promise;
          },
        }
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
      });

    $stateProvider
      .state('collection', {
        url: '/collection/:collectionId',
        controller: 'CollectionCtrl',
        reloadOnSearch : false,
        templateUrl: RUNTIME.static + 'templates/collection.html',
        resolve: {
          collection: function(CollectionFactory, $stateParams) {
            return CollectionFactory.get({id: $stateParams.collectionId}).$promise;
          },
        }
      })
      .state('collection.story', { // i.e the chapters ;)
        url: '/:storyId',
        controller: 'StoryCtrl',
        reloadOnSearch : false,
        templateUrl: RUNTIME.static + 'templates/collection.story.html',
        resolve: {
          story: function(StoryFactory, $stateParams) {
            return StoryFactory.get({id: $stateParams.storyId}).$promise;
          },
        }
      })

    
    $stateProvider
      .state('notifications', {
        abstract: true,
        url: '/notifications',
        controller: 'NotificationsCtrl',
        templateUrl: RUNTIME.static + 'templates/notifications.html',
      })
        .state('notifications.activities', {
          url: '/activities',
          controller: 'ItemsCtrl',
          templateUrl: RUNTIME.static + 'templates/items.html',
          resolve: {
            items: function(PulseFactory) {
              return PulseFactory.activities().$promise;
            },

            model: function() {
              return 'action';
            },
            factory: function(PulseFactory) {
              return PulseFactory.get;
            }
          }
        });
   

      /*
        All the rest are static pages and will download the md files directly
      */
    $stateProvider
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
  })
  .run(function($window, $log, RUNTIME){
    $log.log('☕ app run, version: Happy Crocodile; analytics:', RUNTIME.settings.analytics? 'enabled': 'disabled');
    if(RUNTIME.settings.analytics)
      $window.ga('create', RUNTIME.settings.analytics || 'UA-XXXXXXXX-X', 'auto');
  })

