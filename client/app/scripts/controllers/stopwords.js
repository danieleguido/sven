'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:StopwordsCtrl
 * @description
 * # StopwordsCtrl
 * Controller of the svenClientApp
 */
angular.module('svenClientApp')
  .controller('StopwordsCtrl', function ($scope, $routeParams, $log, StopwordsFactory) {
    $log.debug('StopwordsCtrl ready');
    $scope.stopwords = '';
    $scope.localCorpus = {};
    $scope.lock = false;

    $scope.ace = {
      mode: 'javascript'
    };

    StopwordsFactory.query({id:$routeParams.id}, function(data){
      $log.info('loading documents', data);
      if(typeof data.objects == 'object')
        $scope.stopwords = data.objects.join("\n");
      
      }, function(){
    });

    $scope.save = function() {
      $scope.lock = true;
      $log.info('StopwordsCtrl.save() -->',  $scope.stopwords.substring(0,50).split('\n'));

      StopwordsFactory.save({
        id:$routeParams.id,
        words:$scope.stopwords
      }, function(data) {
        
        $log.info('StopwordsCtrl.save() --> success',  data);
        $scope.stopwords = data.objects.join('\n');
        $scope.lock = false;
      })
    };
    
    
    $scope.$watch('corpora', function(){// pseudo react diff. looking for the local corpus among different corpora
      for(var i=0; i<$scope.$parent.corpora.length; i++) {
        if($scope.$parent.corpora[i].id == $routeParams.id) {
          $scope.$parent.diffclone($scope.localCorpus, $scope.$parent.corpora[i])
        }
      }
    });
  });
