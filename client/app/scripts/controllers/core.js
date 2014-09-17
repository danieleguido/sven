'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:CoreCtrl
 * @description
 * # CoreCtrl
 * Controller of the svenClientApp
 */
angular.module('svenClientApp')
  .controller('CoreCtrl', function ($scope, $log, $upload, $cookies, $timeout, LoginFactory, CommandFactory, NotificationFactory) {
    $log.debug('CoreCtrl ready');
    $scope.status = 'LOADING';
    
    // current corpus
    $scope.corpus = {};

    // current user
    $scope.profile = {};

    // available corpora
    $scope.corpora = [];

    // current jobs
    $scope.jobs = [];

    // repeating
    var corpusId = $cookies.corpusId;

    function tick() {
      NotificationFactory.query({},function(data){
        //todo jobs diff
        if(data.status != "ok" && data.code=='Unauthorized') {
          $scope.status = 'Unauthorized';
        } else {
          $scope.status = 'RUNNING';
        };
        
        if(data.meta.profile.date_last_modified != $scope.profile.date_last_modified)
          $scope.profile = data.meta.profile;

        //$scope.profile.documents = data.objects.reduce(function(a,b){ return a.count.documents + b.count.documents })
        // check if differences
        $scope.corpora = data.objects;
        $scope.jobs = data.jobs;
        // if corpusID choose the corpus matching corpusId, if any. @todo
        var candidate = data.objects.pop();
        
        $scope.corpus = candidate;
        
        $timeout(tick, 4617);
        
      }, function(data){
        $log.error('ticking error',data); // status 500 or 404 or other stuff
        $timeout(tick, 4917);
        $scope.status = 'ERROR';

      }); /// todo HANDLE correctly connection refused
    };
    
    tick(); 

    /*
      handle file upload at upper level
    */
    $scope.uploadingQueue = [];
    var uploaders = {};
    
    var start = function($file, index) {
      uploaders[index] = $upload.upload({
          url: '/api/corpus/' + $scope.corpus.id + '/upload', //upload.php script, node.js route, or servlet url
          file: $file
        }).then(function(res) {
          $scope.uploadingQueue[index].completion = 100;
          console.log(res);
          $log.info('completed', res);
        }, function(response) {
          $log.error(response);
          //if (response.status > 0) $scope.errorMsg = response.status + ': ' + response.data;
        }, function(evt) {
          // Math.min is to fix IE which reports 200% sometimes
          $scope.uploadingQueue[index].completion = Math.min(100, parseInt(100.0 * evt.loaded / evt.total));
        });
    };

    $scope.onFileSelect = function($files) {
      $log.debug('onFileSelect', $files);
      $scope.uploadingQueue = [];
      uploaders = {};

      for ( var i = 0; i < $files.length; i++) {
        var $file = $files[i];
        $scope.uploadingQueue.push({
          size: $file.size,
          name: $file.name,
          type: $file.type,
          index: i,
          completion: 0
        });
        start($file, i);
        
      }
    };

    /*
      @param a valid cmd command to be passed to api/start. Cfr api.py
    */
    $scope.executeCommand = function(cmd, corpus) {
      CommandFactory.query({
        id: corpus.id,
        cmd: cmd
      }, function() {
        console.log(arguments);
      })
    };


    /*
       handle corpus management
    */
    $scope.$watch('corpus', function(){
      if(!$scope.corpus.id || corpusId == $scope.corpus.id)
        return;
      corpusId = $scope.corpus.id; // set cookie please...
      console.log('switch to corpus:', $scope.corpus.name);
    })
    $log.info('corpus id (cookies):', corpusId || 'cookie not set');
  });
