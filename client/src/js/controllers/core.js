'use strict';

var API_PARAMS_CHANGED = 'api_params_changed',
    OPEN_ADD_CORPUS    = 'OPEN_ADD_CORPUS',
    CORPUS_CHANGED     = 'CORPUS_CHANGED',
    OPEN_ATTACH_TAG    = 'OPEN_ATTACH_TAG';


function toast(message, title, options){
  if(!options){
    options={}
  };
  if(typeof title=="object"){
    options=title;
    title=undefined;
  }

  if(options.cleanup!=undefined)
    $().toastmessage("cleanToast");
  var settings=$.extend({
    text: "<div>"+(!title?"<h1>"+message+"</h1>":"<h1>"+title+"</h1><p>"+message+"</p>")+"</div>",
    type: "notice",
    position: "bottom-center",
    inEffectDuration: 200,
    outEffectDuration: 200,
    stayTime: 1900
  },options);

  $().toastmessage("showToast", settings);
};


function cleanToast () {
 $().toastmessage("cleanToast");
};


/**
 * @ngdoc function
 * @name svenClientApp.controller:CoreCtrl
 * @description
 * # CoreCtrl
 * Controller of the svenClientApp
 */
angular.module('sven')
  .controller('CoreCtrl', function ($scope, $location, $log, $upload, $sce, $cookies, $timeout, $filter, CommandFactory, NotificationFactory) {
    $log.debug('CoreCtrl ready');
    $scope.status = 'LOADING';

    
    // current corpus
    $scope.corpus = {};

    // current user
    $scope.profile = {};

    // available corpora
    $scope.corpora = [];

    // if it is true, inside tick function a total replacement of corpus item will be done
    $scope.reload_corpora = true;

    // current jobs
    $scope.jobs = [];

    // current pagination page
    $scope.page = 1;

    // limit result per page
    $scope.limit = 50;

    // offset result per page, internal use
    $scope.offset = 0;

    // number of items for pagination purpose
    $scope.totalItems = 0;

    // current query search
    $scope.search = '';
    // current documents filters (tags, language, date)
    $scope.filters = {};
    $scope.filtersItems = {}; // the collection of actual emlement in order not to reload every time filters vars

    $scope.now = new Date(); // today datetime

    $scope.waitingJob = false; // if set to a specific corpus id, it will listen to it  

    // current documents orderby(s). Watch for $scope.$watch('orderBy.choice') 
    $scope.orderBy = {
      choices: [
        {label:'by date added', value:'-date_created'},
        {label:'by date', value:'date'},
        {label:'by name', value:'name'}
      ],
      choice: {label:'by date added', value:'-date_created'},
      isopen: false,
      direction: true // a-z or false z-a
    };

    // getting the corpus id via cookie
    var corpusId = $cookies.corpusId;

    /*
      Clone source in target by changing only the different fields
    */
    $scope.diffclone = function(target, source) {
      if(!target) {
        target = source;
      } else {
        for(var i in source) {
          if(typeof target[i]=='object') {
            $scope.diffclone(target[i], source[i]);
          } else if(!target[i] || target[i] != source[i]) {//console.log('updtargetted', i);
            target[i] = source[i];
          }
        }
      }
    };


    $scope.html = function(html_code) {
      return $sce.trustAsHtml(html_code);
    }


    function tick() {
      NotificationFactory.query({},function(data){
        var activeJobs = data.jobs.filter(function(d){
          return d.completion != 1
        });
          
        // is there at least a job running? And we're not waiting for it specifically?
        if(!$scope.waitingJob && activeJobs.length) {
          $scope.waitingJob = activeJobs[activeJobs.length - 1].id;
          $log.info('assign the last useful job to waitingJob', $scope.waitingJob)
          
        };

        // store qvqilqble tqg type
        $scope.typesofmedia = data.tags;

        // check status and exablish if a job has been finished
        if($scope.waitingJob) {
          for(var i=0; i < data.jobs.length; i++) {
            if(data.jobs[i].id == $scope.waitingJob) {
              if(data.jobs[i].completion == 1 && data.jobs[i].status == "END") {
                $log.debug('job completed!',data.jobs[i].completion, data.jobs[i].status);
                toast("job completed");
                $scope.waitingJob = false;
              };
            };
          };

        }

        // otherwise, if there are no jobs running ...
        //$scope.waitingJob = false;

        // update profile, if needed
        if(data.meta.profile.date_last_modified != $scope.profile.date_last_modified)
          $scope.profile = data.meta.profile;

        if($scope.reload_corpora || $scope.corpora.length != data.objects.length) {
          $scope.corpora = data.objects;
          $scope.reload_corpora = false;
          cleanToast();
        } else {
          $scope.diffclone($scope.corpora, data.objects);
        }

        

        // check that corpus job completion (or output errors)
        
        // check existence of cookie corpusId

        $scope.jobs = data.jobs;
        // if corpusID choose the corpus matching corpusId, if any. @todo
        var candidate,
            corpus_changed = false;
        for(var i=0; i<data.objects.length;i++) {
          if($cookies.corpusId == data.objects[i].id)
            candidate = data.objects[i];
        }
        if(!candidate)
          candidate = data.objects[data.objects.length-1];

        if(candidate.id != $scope.corpus.id) {
          corpus_changed = true;
        }

        $scope.diffclone($scope.corpus, candidate);
        
        if(corpus_changed)
          $scope.$broadcast(CORPUS_CHANGED);
        // update status and do things
        
        if(data.status != "ok" && data.code=='Unauthorized') {
          $scope.status = 'Unauthorized';
        } else {
          $scope.status = 'RUNNING';
        };
        //$scope.corpus = candidate;
        
        $timeout(tick, 4617);
        
      }, function(data){
        $log.error('ticking error',data); // status 500 or 404 or other stuff
        $timeout(tick, 4917);
        $scope.status = 'ERROR';

      }); /// todo HANDLE correctly connection refused
    };
    
    $timeout(tick, 517);

    /*
      handle file upload at upper level
    */
    $scope.uploadingLoaded = 0;
    $scope.uploadingTotal  = 0;
    $scope.uploadingQueued = 0;
    $scope.uploadingQueue  = 0;
    $scope.uploadingError  = 0;

    $scope.upload = function($files) {
      $log.info('CoreCtrl.upload', $files.length, 'files');

      for(var i = 0; i < $files.length; i++){
        $upload.upload({
          url: SVEN_BASE_URL + '/api/corpus/' + $scope.corpus.id + '/upload', //upload.php script, node.js route, or servlet url
          file: $files[i]
        }).then(function(res) {
          $scope.uploadingLoaded += res.config.file.size;
          $scope.uploadingQueue--;
          $log.log('CoreCtrl.upload', res.config.file.name,'uploaded', res.config.file.size, 'remaining', $scope.uploadingQueue, '', $scope.uploadingLoaded/$scope.uploadingTotal);
          
          if($scope.uploadingQueue == 0) {
            toast('uploaded ' + ($scope.uploadingQueued- $scope.uploadingError) + ' files');
            $scope.$broadcast(API_PARAMS_CHANGED)
          }
        }, function(err){
          $log.error(response);
          $scope.uploadingQueue--;
          $scope.uploadingError++;
          if($scope.uploadingQueue == 0) {
            toast('uploaded ' + ($scope.uploadingQueued- $scope.uploadingError) + ' files');
            $scope.$broadcast(API_PARAMS_CHANGED);

          }
        }, function(evt){
          $log.info(evt);
        });
      };

      // $upload.upload({
      //   url: SVEN_BASE_URL + '/api/corpus/' + $scope.corpus.id + '/upload', //upload.php script, node.js route, or servlet url
      //   file: $file
      // }).then(function(res) {
        
      //   var uploadedFile = $scope.uploadingQueue.filter(function(d){
      //     return d.index == index
      //   })[0];

      //   uploadedFile
      //     $scope.uploadingQueue[index].completion = 100;
      //     $log.info('upload @start completed', res);
      //     toast($scope.uploadingQueue[index].name + ' uploaded');
          
      //     $scope.$broadcast(API_PARAMS_CHANGED)
      //   }, function(response) {
      //     $log.error(response);
      //     //if (response.status > 0) $scope.errorMsg = response.status + ': ' + response.data;
      //   }, function(evt) {
      //     // Math.min is to fix IE which reports 200% sometimes
      //     $scope.uploadingQueue[index].completion = Math.min(100, parseInt(100.0 * evt.loaded / evt.total));
      //   });
    };

    $scope.onFileSelect = function($files) {
      $log.info('CoreCtrl.onFileSelect', $files.length, 'files');
      $scope.uploadingQueue = []

      var total = 0;

      toast('uploading ' + $files.length + ' files...');
      
      for ( var i = 0; i < $files.length; i++) {
        var $file = $files[i];
        total += $file.size;
      };
      
      $scope.uploadingTotal = total;
      $scope.uploadingLoaded = 0;
      $scope.uploadingError  = 0;
      $scope.uploadingQueued = +$files.length;
      $scope.uploadingQueue  = +$files.length;
      
      $log.info('CoreCtrl.onFileSelect to be uploaded:', $scope.uploadingTotal, 'bytes');
      
      $scope.upload($files);
        
      //}
    };
    
    /*
      launch the preview of the csv data
    */
    $scope.onMetadataSelect = function($files) {
      $log.debug('onMetadataSelect', $files);
      //
      $scope.file = $files[0];
      $scope.onMetadataStart();
      return;
      toast('loading preview of the metadata file...');
      var reader = new FileReader();
      reader.onload = function(e){
        $scope.file = $files[0];
        $scope.tsv = e.target.result.replace(/[\n\r]+/g,'\n').split(/[\n\r]/).join('\n');
        
      };
      reader.readAsText($files[0]);
      // debugger
      // leave the file quiet ....
    }

    /*
      once the preview has been validated, the data can be uploaded on server.
    */
    $scope.onMetadataStart = function() {
      $upload.upload({
          url: SVEN_BASE_URL + '/api/import/corpus/' + $scope.corpus.id + '/document', //upload.php script, node.js route, or servlet url
          file: $scope.file
        }).then(function(res) {
          $log.info('completed', res);
          toast(res.config.file.name + ' uploaded...', {cleanToast:true});
        }, function(response) {
          $log.error(response);
          //if (response.status > 0) $scope.errorMsg = response.status + ': ' + response.data;
        }, function(evt) {
          // Math.min is to fix IE which reports 200% sometimes
          console.log(evt);
        });
    }

    
    $scope.changePage = function(page){
      $log.info('changePage', page);
      $scope.page = page;
      $scope.$broadcast(API_PARAMS_CHANGED);
    };


    $scope.changeFilter = function(key, filter, item) {
      $scope.filters[key] = filter;
      $scope.filtersItems[key] = angular.extend({
        filter: filter
      }, item);
      $scope.$broadcast(API_PARAMS_CHANGED);
    };

    $scope.removeFilter = function(key, filter) {
      if($scope.filters[key] == filter) {
        delete $scope.filters[key];
        delete $scope.filtersItems[key];
      };

      $scope.$broadcast(API_PARAMS_CHANGED);
    };

    /*
      Attach to request params the search query
    */
    $scope.changeSearch = function(search) {
      $scope.search = search;
      $location.search('search', search);
      // $scope.$broadcast(API_PARAMS_CHANGED);
    }
    /*
      Orderby set
    */
    $scope.changeOrderBy = function(choice) {
      $log.info('changeOrderBy', choice);
      $scope.page = 1;
      $scope.orderBy.choice = choice;
      $scope.orderBy.isopen = false;
      $scope.$broadcast(API_PARAMS_CHANGED);
    };

    /*
      return a dict object that can be used to call 'glue' api.
      it handles: filters, order_by, search, limit and offset
      according to pagination.
    */
    $scope.getParams = function(params) {
      var params = angular.extend({
        offset: $scope.limit * ($scope.page - 1),
        limit: $scope.limit,
        filters: JSON.stringify(angular.copy($scope.filters)),
        order_by: JSON.stringify($scope.orderBy.choice.value.split('|'))
      }, params);
      if($scope.search.trim().length)
        params.search = $scope.search;
      return params;
    };


    /*
      Call the right api to execute the desired command. At the same time set $scope.waitingJob to true;
      Cfr tick function.
      For a list of all available cmd please cfr. ~/sven/management/start_job.py
      @param cmd - a valid cmd command to be passed to api/start. Cfr api.py
      @param corpus - <Corpus> as command target
    */
    $scope.executeCommand = function(cmd, corpus) {
      if(~~['clean', 'removecorpus'].indexOf(cmd) || confirm('Those actions are classed as dangerous. Beware! Corpus selected: ' + corpus.name))
        CommandFactory.launch({
          id: corpus.id,
          cmd: cmd
        }, function(res) {
          if(res.status=="ok") {
            toast('command started, plase wait ...');
            $scope.waitingJob = res.object.id;
          }
        })
    };



    /*
      
      @param document - instance of <Documents> to attach tag
    */
    $scope.attachTag = function(doc) {
      $scope.$broadcast(OPEN_ATTACH_TAG, doc);
    }

    $scope.addCorpus = function() {
      $log.info('CoreCtrl.addCorpus()')
      
      $scope.$broadcast(OPEN_ADD_CORPUS);
    };

    /*
      Call the right api to execute the desired command.
      For a list of all available cmd please cfr. ~/sven/management/start_job.py
      @param cmd - a valid cmd command to be passed to api/start. Cfr api.py
      @param corpus - <Corpus> as command target
    */
    $scope.getDownloadLink = function(corpus) {
      return 'aa';
    }

    /*
      change the main corpus cookie, enabling upload on it.
    */
    $scope.activate = function(corpus) {
      if($cookies.corpusId == corpus.id) return;
      $cookies.corpusId = corpus.id;
      $scope.reload_corpora = true;
      toast('activating corpus ...', {stayTime: 5000});
    }

    /*
      handle reoute update, e.g on search
    */
    $scope.$on('$routeUpdate', function(next, current) { 
      $log.debug('coreCtrl', '@routeUpdate', next, current);
      $scope.search = current.params.search || '';
      $scope.$broadcast(API_PARAMS_CHANGED);
    });

    

    /*
      handle corpus management
    */
    $scope.$watch('corpus', function(){
      if(!$scope.corpus.id || corpusId == $scope.corpus.id)
        return;
      corpusId = $scope.corpus.id; // set cookie please...
      console.log('switch to corpus:', $scope.corpus.name);
    });

    /*
      handle filters on startup
    */
    var startupParams = $location.search();
    if(startupParams.search)
      $scope.search = startupParams.search;
    //$log.info('corpus id (cookies):', corpusId || 'cookie not set');
  });