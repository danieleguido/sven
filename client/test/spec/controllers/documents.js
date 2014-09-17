'use strict';

describe('Controller: DocumentsCtrl', function () {

  // load the controller's module
  beforeEach(module('svenClientApp'));

  var DocumentsCtrl,
    scope;

  // Initialize the controller and a mock scope
  beforeEach(inject(function ($controller, $rootScope) {
    scope = $rootScope.$new();
    DocumentsCtrl = $controller('DocumentsCtrl', {
      $scope: scope
    });
  }));

  it('should attach a list of awesomeThings to the scope', function () {
    expect(scope.awesomeThings.length).toBe(3);
  });
});
