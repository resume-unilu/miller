/**
 * @ngdoc service
 * @name miller.services
 * @description
 * # core
 * Resource REST API service Factory.
 */
angular.module('miller')
  /*
    Get a list of stories
  */
  .factory('StoryFactory', function ($resource) {
    return $resource('/api/story/:id/', {},{
      update: {
        method:'PUT'
      },
      patch: {
        method:'PATCH'
      }
    });
  })
  .factory('StoryTagsFactory', function ($resource) {
    return $resource('/api/story/:id/tags/', {},{
      update: {
        method:'PUT'
      }
    });
  })
  .factory('StoryDocumentsFactory', function ($resource) {
    return $resource('/api/story/:id/documents/', {},{
      update: {
        method:'PUT'
      }
    });
  })
  .factory('ProfileFactory', function ($resource) {
    return $resource('/api/profile/:username/', {},{
      update: {
        method:'PUT'
      },
      patch: {
        method:'PATCH'
      }
    });
  })
  /*
    get a list of ralreeady saved document accessible by the user
  */
  // http://localhost:8888/api/document/
  .factory('DocumentFactory', function ($resource) {
    return $resource('/api/document/:id/', {},{
      update: {
        method:'PUT'
      }
    });
  })
  .factory('CaptionFactory', function ($resource) {
    return $resource('/api/caption/:id/', {},{
      update: {
        method:'PUT'
      },
      patch: {
        method:'PATCH'
      }
    });
  })
  /*
    list tags
  */
  .factory('TagFactory', function ($resource) {
    return $resource('/api/tag/:id/', {},{
      update: {
        method:'PUT'
      }
    });
  })
  /*
    get static pages
  */
  .factory('PageFactory', function ($http, RUNTIME) {
    return {
      get: function(params) {
        return $http.get(RUNTIME.static + 'pages/' + params.name + '.md');
      }
    };
  })

  /*
    Apply MLA or other citation style
  */
  .service('bibtexService', function($filter) {
    return function(json){

    }
  })
  .service('markdownItService', function($filter) {
    return function(value, language){
      var results,
          sections, // document sections.
          md = new window.markdownit(),
          linkIndex = 0;

      // set initial value for results
      results = {
        md: value,
        html:'',
        ToC: [],
        docs: [],
        footnotes: {}
      };
      // load footnotes plugin
      md
        .use(window.markdownitFootnote);

      // rewrite links
      md.renderer.rules.link_open = function(tokens, idx){
        var url = tokens[idx].attrGet('href');
        console.log(url)
        if(url.trim().indexOf('doc/') === 0){
          var documents = url.trim().replace('doc/','').split(',');
          for(var i in documents){
            results.docs.push({
              _index: 'link-' + (linkIndex++), // internal id
              citation: tokens[idx + 1].content,
              slug: documents[i]
            });
          }
          return '<a name="'+ documents[0] +'" ng-click="fullsize(\'' +url+'\', \'doc\')"><span class="anchor-wrapper"></span>';
          // return '<a name="' + documents[0] +'" ng-click="hash(\''+url+'\')"><span class="anchor-wrapper"></span>'+text+'</a>';
        } else if(url.trim().indexOf('voc/') === 0){
          var terms = url.trim().replace('voc/','').split(',');
          for(var i in terms){
            docs.push({
              _index: 'link-' + (linkIndex++), // internal id
              citation: tokens[idx + 1].content,
              slug: terms[i],
              type: 'glossary'
            });
          }
          tokens[idx].attrSet('class', 'glossary');
          return '<a class="glossary" name="'+ documents[0] +'" ng-click="fullsize(\'' +url+'\', \'voc\')"><span class="anchor-wrapper"></span>';
        }  
      };

      md.renderer.rules.heading_open = function(tokens, idx){
        var text = tokens[idx+1].content,
            h = {
              text: text,
              level: tokens[idx].level + 1,
              slug: $filter('slugify')(text)
            };

        results.ToC.push(h);

        return '<h' + h.level + '><div class="anchor-sign" ng-click="hash(\''+ h.slug +'\')"><span class="icon-link"></span></div><a name="' + h.slug +'" class="anchor" href="#' + h.slug +'"><span class="header-link"></span></a>';

      }

      // change rules
      md.renderer.rules.footnote_ref = function render_footnote_ref(tokens, idx, options, env, slf) {
        var id = slf.rules.footnote_anchor_name(tokens, idx, options, env, slf);
        var caption = slf.rules.footnote_caption(tokens, idx, options, env, slf);

        return '<span class="footnote-ref"><a href="#fn' + id + '" id="fnref' + id + '">' + caption + '</a></span>';
      };

      // split sections (main content and footnotes)
      sections = _(value.split(/\s*[-_]{3,}\s*/)).value();

      console.log('markdownItService', sections.length)
      // get the last section (bibliographic footnotes will be there)
      if(sections.length > 1){
        results.footnotes = sections.pop();
        console.log('markedService footnotes: ', results.footnotes)
        // override value with the reduced content
        value = sections.join('');
        // console.log('markedService footnotes: ', value)
      }

      // split value according to language if available (reduce pairs)
      if(language){
        var candidate = _(value.split(/<!--\s*(lang:[a-zA-Z_]{2,5})\s*-->/))
          .compact()
          .chunk(2)
          .fromPairs()
          .value();
        // console.log(language, candidate)
        if(candidate['lang:'+language]) {
          value = candidate['lang:'+language];
        }
        //value = value.split();
      }

      // modify results
      results.html = md.render(value);

      return results
    }
  })
  /*
    Apply marked service for custom markdown ;) Handle with care
    Example on footnotes handling, based on pandoc definition:
    ```
    Here is a footnote reference,[^1] and another.[^longnote]
 
    [^1]: Here is the footnote.
     
    [^longnote]: Here's one with multiple blocks.
        Subsequent paragraphs are indented to show that they belong to the previous footnote.
    ```
  */
  .service('markedService', function($filter) {
    return function(value, language){
      var renderer = new marked.Renderer(),
          linkIndex = 0,
          result = '',
          ToC = [],
          docs = [],
          footnotes = [];

      // split the links section and the footnotes
      var sections = _(value.split(/\s*[-_]{3,}\s*/)).value();
      console.log('markedService', sections.length)
      // get the last section (bibliographic footnotes will be there)
      if(sections.length > 1){
        var footnotes = sections.pop();
        console.log('markedService footnotes: ', footnotes)
        value = sections.join('');
        // console.log('markedService footnotes: ', value)


      }

      // split value according to language(reduce pairs)
      if(language){
        var candidate = _(value.split(/<!--\s*(lang:[a-zA-Z_]{2,5})\s*-->/))
          .compact()
          .chunk(2)
          .fromPairs()
          .value();
        // console.log(language, candidate)
        if(candidate['lang:'+language]) {
          value = candidate['lang:'+language];
        }
        //value = value.split();
      }

      

      // render the footnotes

      // collect h1,h2, hn and get the table of contents ToC
      renderer.heading = function(text, level){
        var h = {
          text: text,
          level: level,
          slug: $filter('slugify')(text)
        };

        ToC.push(h);

        return '<h' + level + '><div class="anchor-sign" ng-click="hash(\''+ h.slug +'\')"><span class="icon-link"></span></div><a name="' + h.slug +'" class="anchor" href="#' + h.slug +'"><span class="header-link"></span></a>' + 
          text + '</h' + level + '>';
      };

      // collect miller document
      renderer.link = function(url, boh, text) {
        console.log('markedService link', url);
        if(url.trim().indexOf('doc/') === 0){
          var documents = url.trim().replace('doc/','').split(',');
          for(var i in documents){
            docs.push({
              _index: 'link-' + (linkIndex++), // internal id
              citation: text,
              slug: documents[i]
            });
          }
          return '<a name="' + documents[0] +'" ng-click="hash(\''+url+'\')"><span class="anchor-wrapper"></span>'+text+'</a>';
        } else if (url.trim().indexOf('voc/') === 0){
          var terms = url.trim().replace('voc/','').split(',');
          for(var i in terms){
            docs.push({
              _index: 'link-' + (linkIndex++), // internal id
              citation: text,
              slug: terms[i],
              type: 'glossary'
            });
          }
          return '<a class="glossary" name="' + terms[0] +'" ng-click="hash(\''+url+'\')"><span class="anchor-wrapper"></span>'+text+' <span class="icon icon-arrow-right-circle"></span></a>';
        
        }
        return '<a href='+url+'>'+text+'</a>';
      };

      renderer.image = function(src, title, alt){
        if((alt||'').indexOf('profile/') === 0){
          return '<div class="profile-thumb" style="background-image:url('+src+')"></div>';
        }
        return '<img src="'+ src+ '" title="'+title+'" alt="'+alt+'"/>';
      };

      // get the new documents and save them in background if needed.
      result = marked(value, {
        renderer: renderer
      });

      return {
        html: result,
        md: value,
        ToC: ToC,
        docs: docs
      };
    }; 
  });