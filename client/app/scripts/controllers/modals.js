'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:StopwordsCtrl
 * @description
 * # ModalTagCtrl
 * Controller of the svenClientApp
 */
angular.module('svenClientApp')
  .controller('AttachTagCtrl', function ($scope, $modalInstance, item) {
    $scope.item = item;

    $scope.ok = function () {
      $modalInstance.close();
    };

    $scope.cancel = function () {
      $modalInstance.dismiss('cancel');
    };
  })
  .controller('ModalTagCtrl', function ($scope, $routeParams, $log, $modal) {
    

    var attachtag;

    $scope.$on(OPEN_ATTACH_TAG, function(e,doc) {
      attachtag = $modal.open({
        templateUrl: 'myModalContent.html',
        controller: 'AttachTagCtrl',
        backdrop:false,
        size: 'sm',
        resolve: {
          item: function () {
            return doc;
          }
        }
      });
    });
  })
  ;