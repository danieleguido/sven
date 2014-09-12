'use strict';

var CTRL_LOADED = 'background: lime; color: #181818',
    STYLE_INFO = 'color: #b8b8b8',

    // events
    CONTROLLER_PARAMS_UPDATED = "CONTROLLER_PARAMS_UPDATED",
    JOBS_RUNNING = 'JOBS_RUNNING',
    UPDATE_STATUS = 'UPDATE_STATUS',

    // common funcitons
    gimmesize = function(obj) {
      var obj = angular.copy(obj),
          size = 0,
          key;

      for (key in obj) {
        if (obj.hasOwnProperty(key))
          size++;
      };
      return size;
    };



angular.module('sven.controllers', ['angularFileUpload'])
  /*
    
    The very main controller. Handle django orm filters in ng-view .
    ===
    
    limit and offset of the curtrent view are also set.
  */
  .controller('layoutCtrl', ['$scope', '$rootScope','$location', '$route', 'TagListFactory', 'ToastFactory', function($scope, $rootScope, $location, $route, TagListFactory, ToastFactory) {

    $scope.limit = 25;
    $scope.offset= 0;
    $scope.default_limit = 25;
    $scope.default_offset = 0;
    
    $scope.filters = {};
    $scope.query = '';
    
    $scope.numofpages = 0;
    $scope.page = 0;
    console.log('%c layoutCtrl ', CTRL_LOADED);
  
    
    $scope.ctrl = ''; // current view controller
    // look after the current corpus, babe.
    
    $scope.toast = function(message, title, options) {
      ToastFactory.toast(message, title, options);
    };

    $scope.toast('sven loaded correctly', {position: 'middle-center'});

    $scope.setCorpus = function(id) {
      $rootScope.selected_corpus_id = id;
    };

    $scope.follow = function(link) {
      //alert(link)
      var path = Array.prototype.slice.call(arguments).join('/').replace(/\/+/g,'/');
      $location.path(path);
    };
    
    $scope.search = function(query) {
      if(query)
        $scope.query = query;
      console.log("%c search ", 'color:white; background-color:#383838', $scope.query);
      $scope.limit = $scope.default_limit;
      $scope.offset = $scope.default_offset;
      $location.search({
        'search': $scope.query
      });
    };

    $scope.pageto = function(page) {
      var page = Math.max(0, Math.min(page, $scope.numofpages));
      console.log('page to', page);
      $scope.offset = page * $scope.limit;
      $scope.distill(); // normally the ctrl is the current ctrl...
    };


    $scope.nextPage = function() {
      $scope.pageto(+$scope.page + 1);
    };
            

    $scope.prevPage = function() {
      $scope.pageto(+$scope.page - 1);
    };


    $scope.paginate = function(options) {
      var options = options || {},
          pages = [],
          left = 0,
          right = 0;

      $scope.total_count = options.total_count;
      console.log('$scope.paginate', $scope.limit, $scope.offset);
      
      $scope.numofpages = Math.floor(($scope.total_count-1) / $scope.limit );
      $scope.page = Math.floor($scope.offset / $scope.limit);

      if($scope.numofpages < 10) {
        left = 0;
        right = +$scope.numofpages;
      } else{
        right = Math.min($scope.numofpages, $scope.page<10?10:$scope.page + 5);
        left = right - 10;
      }

      for(var i=left; i<right+1; i++)
        pages.push(i+1);

      $scope.pages = pages;
      console.log('$scope.paginate', pages);
    };



    $scope.suggestTags = function(tag_type, tag_val) {
      return TagListFactory.query({
          filters:'{"type":"'+tag_type+'"}',
          search:tag_val
      }).$promise.then(function(data) {
        return data.objects;
      });
    };



    $scope.distill = function(options) {
      var candidates = $location.search().filters,
          query = $location.search().search,
          orderby = $location.search().orderby;

      if(query)
        $scope.query = query;
      

      if(candidates) {
        try{
          var filters = JSON.parse(candidates);
          $scope.filters = filters;
        } catch(e){
          console.log("%c! distill: filters failed ", 'color:white; background-color:crimson', e.message);
          
        }
      } else {
        $scope.filters = {};
      }

      $scope.howmanyfilters = gimmesize($scope.filters);

      console.log("%c distill: loading filters ", 'color:white; background-color:green', 'query:',$scope.query, $scope.offset, $scope.limit);   
      $scope.$broadcast(CONTROLLER_PARAMS_UPDATED, options);
    };


    $scope.setProperties = function(property, value) {
      $scope.filters[property] = [value];
      console.log('%c filters setProperties', STYLE_INFO, property, value, $scope.filters);
      $scope.limit = $scope.default_limit;
      $scope.offset = $scope.default_offset,
        
      $location.search({
        'filters': JSON.stringify($scope.filters)
      });
    };


    $scope.setProperty = function(property, value) {
      $scope.filters[property] = value;
      console.log('%c filters setProperty', 'background: crimson; color: white',property, value, $scope.filters);
      $location.search('filters', JSON.stringify($scope.filters))
    };


    $scope.removeProperty = function(property, value) {
      console.log('removing', property, value, 'from filters');
      delete $scope.filters[property];
      $location.search({
        'filters': JSON.stringify($scope.filters)
      });
    }


    $scope.extendFilters = function(filter) {
      var filters = angular.extend({}, $scope.filters, filter);
      return JSON.stringify(filters)
    };

    // LISTENERS
    $rootScope.$on('$routeChangeSuccess', function(e, r){
      console.log("%c    route change success", STYLE_INFO);
      $scope.filters = {};
      $scope.limit = $scope.default_limit;
      $scope.offset = $scope.default_offset;
      $scope.ctrl = String(r.$$route.controller);
      $scope.distill(); // reload filters directly form the params
    });


    $rootScope.$on('$routeUpdate', function(e, r){
      console.log("%c route updated", STYLE_INFO);
      $scope.distill(); // push current controllername
    });
  }])
  /*
    global rapid visualizations
  */
  .controller('indexCtrl', ['$scope', 'D3Factory', function($scope, D3Factory) {
    $scope.values = {timeline:[]};
    
    D3Factory.timeline({},function(data) {
      $scope.values.timeline = data.values;
    });

  }])
  /*

    notificationCtrl. Probably better with webworker, even better with socket
    ===
  */
  .controller('notificationCtrl', ['$rootScope', '$scope', '$log', '$timeout', 'NotificationFactory', function($rootScope, $scope, $log, $timeout, NotificationFactory) {
    $scope.jobs = {}; // active jobs only...
    $scope.has_active_jobs = false;
    function tick() {
      NotificationFactory.query({id: $scope.job_id}, function(data){
        //todo jobs diff
        for(var i=0; i<data.objects.length; i++) {
          console.log(data.objects[i], data.objects[i].completion);
          if(data.objects[i].completion != 1)
            $scope.jobs[data.objects[i].id] = data.objects[i];

        };

        console.log(data.objects, data.meta)
        $timeout(tick, 3617);
        $rootScope.$emit(JOBS_RUNNING, data);

      }, function(data){
        $scope.jobs = [];
        $log.info('ticking error',data); // status 500 or 404 or other stuff
        $timeout(tick, 3917);
      }); /// todo HANDLE correctly connection refused
    };
    
    tick(); // once done, allorw syncing in other controllers!

    $log.info('%c notificationCtrl ', CTRL_LOADED);
  }])
  /*

    Sidebar user corpora ctrl.
    ===
  */
  .controller('corpusListCtrl', ['$scope', 'CorpusListFactory', function($scope, CorpusListFactory) {
    
    $scope.sync = function() {
      CorpusListFactory.query(function(data){
        $scope.items = data.objects;
      });
    };
    
    $scope.sync();
    console.log('%c corpusListCtrl ', CTRL_LOADED);
  }])
  /*

    Monitor: enable analysis and check global log file
    ===
  */
  .controller('monitorCtrl', ['$rootScope','$scope','$routeParams', '$log', 'CommandFactory', function($rootScope, $scope, $routeParams, $log, CommandFactory) {
    $log.info('%c monitorCtrl ', CTRL_LOADED);

    $scope.job = {}; // current corpus monitoring

    $rootScope.$on(JOBS_RUNNING, function(e, data) {
      $scope.corpus_id = $routeParams.corpus_id; // or guess

      $scope.log = data.log;
      // console.log(data);
      for(var i in data.objects) {
        if(data.objects[i].corpus.id == $scope.corpus_id) {
          $scope.job = data.objects[i];
          break;
        }
      }; // change what needs to be changed @todo
      
    })

    $scope.setCorpus($routeParams.corpus_id);

    /*
      @param a valid cmd command to be passed to api/start. Cfr api.py
    */
    $scope.start = function(cmd) {
      CommandFactory.query({
        id: $routeParams.corpus_id,
        cmd: cmd
      }, function() {
        console.log(arguments);
      })
    };

  }])
  /*

    Document list for a single corpus
    ===
  */
  .controller('documentListCtrl', ['$scope', '$rootScope', '$modal', '$log', '$upload', '$routeParams', 'DocumentListFactory', 'DocumentFactory', 'DocumentTagsFactory', function($scope, $rootScope, $modal, $log, $upload, $routeParams, DocumentListFactory, DocumentFactory, DocumentTagsFactory) {
    
    $scope.sync = function() {
      DocumentListFactory.query({id: $routeParams.id, limit:$scope.limit, offset:$scope.offset, filters:$scope.filters}, function(data){
          console.log(data);
          $scope.items = data.objects;
          $scope.paginate({
            total_count: data.meta.total_count
          });
      });
      $scope.setCorpus($routeParams.id); // explicit corpus id assignment
    };


    /*
      Opena a modal with a tag selector.
      @param doc - the angular item mapping a sven document
    */
    $scope.tag = function(doc) {
      var modalInstance = $modal.open({
        templateUrl: 'static/partials/modals/tag.html',
        controller: function ($scope, $modalInstance, items) {
          
          $scope.ok = function () {
            $modalInstance.close($scope.selected.item);
          };

          $scope.cancel = function () {
            $modalInstance.dismiss('cancel');
          };
        },
        size: 'sm',
        backdrop: true,
        resolve: {
          items: function () {
            return $scope.items;
          }
        }
      });
      modalInstance.result.then(function (selectedItem) {
        $scope.selected = selectedItem;
      }, function () {
        $log.info('Modal dismissed at: ' + new Date());
      });

    };
    /*
      Remove the selected ID after a simpe confirm action
    */
    $scope.remove = function(doc) {
      if(confirm("Do you really want to delete document '" + doc.name + "'?")){
        DocumentFactory.remove({
          id: doc.id
        }, function(data) {
          for(var i in $scope.items) {
            $scope.items[i].id == doc.id && $scope.items.splice(i, 1);
          }
          
          $scope.paginate({
            total_count: data.meta.total_count
          });   
        })
      };
    };


    $scope.uploadprogress = false;
    $scope.total = 0;
    $scope.loaded = 0;


    $scope.onFileSelect = function($files) {
      $log.info('onFileSelect', $files);
      $rootScope.$emit(UPDATE_STATUS, 'starting upload...');
      // do not accept files while uploading...
      var numfiles = $files.length,
          queue = {},
          getQueueProgress = function(){
            var l = 0,
                t = 0;
            console.log('@getQueueProgress', queue)
            for(var i in queue) {
              l += queue[i].loaded;
              t += queue[i].expected;
            }
            return t==0? 0: parseInt(l*10000/t)/100;
          },
          getQueueErrors = function() {

          },
          queueLoading = function() {
            $scope.uploadprogress = getQueueProgress();
            $log.info('@queueLoading',$scope.uploadprogress, queue);
            if($scope.uploadprogress == 100)
              queueLoaded();
          },
          queueLoaded = function() {
            $log.info('@queueloaded',$scope.uploadprogress, queue);
            $scope.toast('upload completed', {position: 'middle-center'});
            $scope.sync();
            $scope.uploadprogress = false;
          };

      $scope.uploadprogress = '0.0';
      
      for (var i = 0; i < numfiles; i++) {
        var file = $files[i];
        
        queue[''+file.name] = {
          loaded:0,
          expected:file.size,
          index: i
        };
      };
      console.log('aodapdapdoapodapda',queue);
      // separate call for each file here... sorry...
      for (var name in queue) {
        $scope.upload = $upload.upload({
          url: '/api/corpus/' + $routeParams.id + '/upload', //upload.php script, node.js route, or servlet url
          // method: POST or PUT,
          // headers: {'headerKey': 'headerValue'},
          // withCredentials: true,
          data: {},
          file: $files[queue[name].index],
          //file: $files, //upload multiple files, this feature only works in HTML5 FromData browsers
          /* set file formData name for 'Content-Desposition' header. Default: 'file' */
          //fileFormDataName: myFile, //OR for HTML5 multiple upload only a list: ['name1', 'name2', ...]
          /* customize how data is added to formData. See #40#issuecomment-28612000 for example */
          //formDataAppender: function(formData, key, val){} //#40#issuecomment-28612000
        }).progress(function(evt) {
          console.log('progress', name, evt);
          //queue[''+file.name].loaded = evt.loaded;
          queueLoading();

        }).success(function(data, status, headers, obj) {
          // file has been uploaded successfully !
          console.log('success', name, arguments);
          queue[''+obj.file.name].loaded = obj.file.size;
          queueLoading();

          //$rootScope.$emit(UPDATE_STATUS, '');
          //$scope.toast('upload completed', {position: 'middle-center'});
          //$scope.sync();

        }).error(function(data, status, headers, obj){
          queue[''+obj.file.name].expected = 0;
          queue[''+obj.file.name].error = 'error';
          console.log('error uploading', obj.file.name,'',arguments);
          queueLoading();
        });
        //.error(...)
        //.then(success, error, progress); 
      }
    // $scope.upload = $upload.upload({...}) alternative way of uploading, sends the the file content directly with the same content-type of the file. Could be used to upload files to CouchDB, imgur, etc... for HTML5 FileReader browsers. 
    };

    $scope.$on(CONTROLLER_PARAMS_UPDATED, function(e, options) {
      $scope.ctrl == 'documentListCtrl'
        && $scope.sync();
    });

    $scope.sync();

    $scope.__adding_tag = false;
    $scope.attachTag = function(tag_type, tag, item) {
      DocumentTagsFactory.save({
        id: item.id
      }, {
        tags: tag.name || tag,
        type: tag_type
      },function(data){
        $scope.sync();     
      });
      $scope.__tag_candidate = "";
      $scope.__adding_tag = false;
      console.log(arguments, $scope.__tag_candidate);
    };


    $log.info('%c documentListCtrl ', CTRL_LOADED, 'loaded');
  }])
  /*
    
    DocumentCtrl
    ---
    
    load or add a brand new document

  */
  .controller('documentCtrl', ['$scope', '$upload', '$routeParams', '$location', 'DocumentFactory', 'DocumentListFactory', 'DocumentSegmentsFactory', '$log', function($scope, $upload, $routeParams, $location, DocumentFactory, DocumentListFactory, DocumentSegmentsFactory, $log) {
    $scope.document = {
      mimetype: 'text/html'
    };
    $scope.segments = [];


    $scope.sync = function() {
      DocumentFactory.query({id: $routeParams.id}, function(data){
        $scope.document = data.object;
        
        DocumentSegmentsFactory.query({id: $routeParams.id}, function(data){
          console.log(data);
          $scope.segments = data.objects
        })
      });
    };


    $scope.save = function() {
      if(!$routeParams.corpus_id)
        return;
      $scope.toast('saving link ...');
      $log.info('documentCtrl save()', angular.copy($scope.document));
      
      var params = angular.copy($scope.document);

      if(!params.name)
        params.name = params.url
          .replace(/http:\/\/w+/g,'')
          .replace(/[^\w]/g, ' ')
          .replace(/\s+/g,' ')
          .trim().substring(0,64);

      DocumentListFactory.save(
        {
          id: $routeParams.corpus_id
        },
        params,
        function(data) {
          console.log(data);
          $scope.toast('link saved',{});
          $location.path('/document/' + data.object.id);
          // redirect to new document
        }
      );
    };

    /*
      Upload txt version of the file.
    */
    $scope.onFileSelect = function($files) {
      for (var i = 0; i < $files.length; i++) {
        var file = $files[i];
        $scope.upload = $upload.upload({
          url: '/api/document/' + $routeParams.id + '/upload', //upload.php script, node.js route, or servlet url
          file: file,
        }).progress(function(evt) {
          $scope.uploadprogress = parseInt(100.0 * evt.loaded / evt.total)
          console.log('percent: ' + $scope.uploadprogress);
        }).success(function(data, status, headers, config) {
          // file is uploaded successfully
          $scope.uploadprogress = 100;
          
          console.log('percent: ' + $scope.uploadprogress);
          console.log(data);
          $scope.document.text = data.object.text
        });
        //.error(...)
        //.then(success, error, progress); 
      }
    // $scope.upload = $upload.upload({...}) alternative way of uploading, sends the the file content directly with the same content-type of the file. Could be used to upload files to CouchDB, imgur, etc... for HTML5 FileReader browsers. 
    };

    $routeParams.id && $scope.sync();
    $routeParams.corpus_id && $scope.setCorpus($routeParams.corpus_id);// add new docuemnt to a given corpus

    $log.info('documentCtrl loaded');
  }])
  .controller('searchCtrl', ['$scope', '$log', 'DocumentListFactory', function($scope, $log, DocumentListFactory) {
    $log.info('searchCtrl loaded');

  }])
  .controller('contextCtrl', ['$scope', function($scope) {


  }])
  /*
    Profile controller
  */
  .controller('profileCtrl', ['$scope', 'ProfileFactory', function($scope, ProfileFactory) {
    $scope.sync = function(){
      ProfileFactory.query({}, function(data) {
        console.log(data);
        $scope.profile = data.object;
      });
    };

    $scope.save = function() {
      ProfileFactory.save(angular.copy($scope.profile), function(data) {
        console.log('back to me',data);
        $scope.profile = data.object;
      });
    }
    $scope.sync();
    console.log('%c profileCtrl ', CTRL_LOADED);
  }])
  /*
    Segmentlist controller, with attach tag.
  */
  .controller('segmentListCtrl', ['$scope','$routeParams', 'SegmentListFactory', 'SegmentFactory', function($scope, $routeParams, SegmentListFactory, SegmentFactory) {
    $scope.sync = function() {
      SegmentListFactory.query({id: $routeParams.id, limit:$scope.limit, offset:$scope.offset, filters:$scope.filters}, function(data) {
          console.log(data);
          $scope.items = data.objects;
          $scope.paginate({
            total_count: data.meta.total_count
          });
      });
      $scope.setCorpus($routeParams.id); // explicit corpus id assignment
    };

    $scope.save = function(item) {
      SegmentFactory.save({
        corpus_id: $routeParams.id,
        segment_id: item.id
      }, {
        status: item.status,
        cluster: item.cluster
      }, function(data) {
        console.log(data);

      })
    }
    $scope.toggleStatus = function(item) {
      
      if(item.status == 'IN')
        item.status = 'OUT';
      else
        item.status = 'IN';
      $scope.save(item);
    }

    $scope.$on(CONTROLLER_PARAMS_UPDATED, function(e, options) {
      $scope.ctrl == 'segmentListCtrl'
        && $scope.sync();
    });

    $scope.sync();
    console.log('%c segmentListCtrl ', CTRL_LOADED);
  }])
  /*
    Independent controller, change the header 'what I m doing' message with 
    something more appropriate
  */
  .controller('statusCtrl', ['$scope', '$rootScope', '$log', function($scope, $rootScope, $log) {
    $scope.message = ''
    $rootScope.$on(UPDATE_STATUS, function(e, message) {
      $scope.message = message;
    });
    $log.info('%c statusCtrl ', CTRL_LOADED);
  }])
  /*
    Add twitter account to be monitored to the current corpus
  */
  .controller('twitterCtrl', ['$scope', '$log', '$routeParams', 'TwitterListFactory', function($scope, $log, $routeParams, TwitterListFactory) {

    $scope.item = {};

    $scope.setCorpus($routeParams.corpus_id); // last corpus id

    $scope.save = function(item) {
      TwitterListFactory.save({},{
        corpus: $routeParams.id,
        url: $scope.item.url
      }, function(data) {
        $scope.toast('twitter account added to queue !');
        console.log(data);
      })
    };
    $log.info('%c twitterCtrl ', CTRL_LOADED);
    
  }])
  /*
    A dummy, blank controller
  */
  .controller('blankCtrl', ['$scope', function($scope) {


  }])